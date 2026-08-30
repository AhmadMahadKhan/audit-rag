

"""
AI-based document classification using Ollama.

CLASSIFICATION STRATEGY
-----------------------
The previous implementation classified PDFs using ONLY the first page.
That is unreliable for long documents such as:

    - 10-K / 10-Q filings
    - audit reports
    - contracts
    - financial statements
    - manuals
    - policies

This version uses a richer document preview.

For PDFs:
    1. Extract text from the first several pages.
    2. If those pages contain insufficient text, sample additional pages.
    3. For long documents, sample pages from:
         - beginning
         - early section
         - middle
         - later section
         - end
    4. Convert the selected text into a bounded word-based preview.
    5. Send the preview to Ollama.

For TXT/MD:
    - Read the beginning of the document.
    - Use up to MAX_PREVIEW_WORDS words.

For DOCX:
    - Extract paragraph text.
    - Use up to MAX_PREVIEW_WORDS words.

IMPORTANT
---------
This is still a PRE-PARSE / upload-time classifier.

The real parser should still call:

    classify_text(parsed_text)

after the parsing stage if you want full-document classification.

The upload-time classifier is intentionally lightweight so that
classification does not require processing the entire document.

Why word-based instead of character-based?
-------------------------------------------
The old code used:

    text[:2000]

That means approximately 2,000 CHARACTERS, not 2,000 words.

This implementation uses:

    MAX_PREVIEW_WORDS = 3000

which gives the model substantially more useful information while
still keeping the prompt bounded.

Fallback strategy
-----------------
If the PDF has very little text:

    first pages
        ↓
    sampled pages
        ↓
    metadata / filename

If a scanned PDF has no extractable text, OCR should ideally happen
in the parsing/OCR stage and the resulting parsed text should then
be passed to classify_text().
"""

import io
import json
import math
from typing import List

import httpx

from app.classification.base import BaseClassifier, ClassificationResult
from app.classification.document_types import DOCUMENT_TYPES
from app.core.config import settings
from app.core.logging_config import logger


# ============================================================================
# CONFIGURATION
# ============================================================================

# Ollama classification model.
#
# Keep this configurable through your application settings.
MODEL = settings.CLASSIFICATION_MODEL

# Maximum number of WORDS sent to the classifier.
#
# This is intentionally word-based rather than character-based.
MAX_PREVIEW_WORDS = 25000

# Minimum amount of useful text we want from the first pages.
#
# If we cannot get approximately this much text, we sample more pages.
MIN_INITIAL_WORDS = 25000

# Maximum number of PDF pages to inspect during cheap classification.
#
# We do NOT want to parse hundreds of pages just to classify a document.
MAX_PDF_PAGES_TO_INSPECT = 40

# Number of first pages to inspect first.
INITIAL_PDF_PAGES = 15

# Maximum characters we allow from a single page.
#
# This prevents one extremely dense page from consuming the whole preview.
MAX_CHARS_PER_PAGE = 18000

# Ollama timeout.
OLLAMA_TIMEOUT_SECONDS = 60.0


# ============================================================================
# SYSTEM PROMPT
# ============================================================================

SYSTEM_PROMPT = """You are a strict document classification engine used in
an automated document intelligence pipeline.

Your ONLY job is to assign exactly one document type label to the document
text you are given.

RULES YOU MUST FOLLOW:

1. You MUST choose the type from the ALLOWED TYPES list below.

2. Never invent a new label.

3. Never modify the spelling or case of a label.

4. If the text does not clearly match any type, respond with:
   "unknown"

5. Do NOT guess just to avoid "unknown".

6. Base confidence on how certain you are:

   0.90 - 1.00
       Explicit and unambiguous markers.
       Example:
       "INVOICE", invoice number, line items, amount due.

   0.60 - 0.89
       Strong contextual evidence but no explicit document label.

   0.30 - 0.59
       Weak or partial evidence.

   0.00 - 0.29
       Very little useful evidence.
       Usually use "unknown".

7. The document excerpt may contain text from multiple pages.
   Use the overall evidence rather than relying only on the first line.

8. Financial filings such as 10-K and 10-Q documents should generally be
   classified according to the available financial-document categories.

9. Output ONLY one JSON object.

10. Do NOT output markdown.

11. Do NOT output explanations.

12. Do NOT output text before or after the JSON.

13. The JSON MUST contain exactly two keys:

       "type"
       "confidence"

14. "confidence" must be a number between 0.0 and 1.0.

ALLOWED TYPES:

{type_descriptions}

Example valid response:

{{"type": "invoice", "confidence": 0.92}}
"""


USER_PROMPT_TEMPLATE = """Classify the following document.

The text below may contain excerpts from multiple pages of the same
document.

Use the overall evidence to determine the most appropriate document type.

--- DOCUMENT EXCERPT START ---

{text}

--- DOCUMENT EXCERPT END ---

Respond with the JSON object only.
"""


# ============================================================================
# HUMAN-READABLE DOCUMENT TYPE DESCRIPTIONS
# ============================================================================

TYPE_DESCRIPTIONS = {
    "invoice": (
        "A bill requesting payment for goods or services, usually containing "
        "an invoice number, line items, amounts, tax, subtotal, or amount due"
    ),

    "receipt": (
        "Proof of a completed payment or purchase, usually containing "
        "items purchased, transaction information, and total paid"
    ),

    "purchase_order": (
        "A buyer's formal request to a supplier to purchase goods or services, "
        "usually containing a PO number and ordered items"
    ),

    "bank_statement": (
        "A bank-issued summary of an account's transactions over a period, "
        "including deposits, withdrawals, balances, and transaction dates"
    ),

    "financial_statement": (
        "Formal financial reporting documents such as balance sheets, "
        "income statements, cash flow statements, or statements of equity"
    ),

    "tax_document": (
        "Tax forms or tax filings such as W-2, 1099, tax returns, or "
        "other government tax documents"
    ),

    "contract": (
        "A legally binding agreement between parties, such as an NDA, "
        "service agreement, employment agreement, or vendor contract"
    ),

    "policy": (
        "An internal or external policy, procedure, standard, rule, "
        "or organizational guideline"
    ),

    "manual": (
        "An instructional or reference guide, handbook, user manual, "
        "technical manual, or operating guide"
    ),

    "audit_report": (
        "A formal report documenting audit procedures, findings, opinions, "
        "control deficiencies, or audit conclusions"
    ),

    "hr_document": (
        "Employee or human-resources related documents such as offer letters, "
        "onboarding documents, payroll documents, or employee records"
    ),

    "email": (
        "An email message containing sender, recipient, subject, "
        "message body, or email metadata"
    ),

    "html": (
        "Generic HTML/web content that does not match a more specific "
        "document type"
    ),

    "spreadsheet": (
        "Generic spreadsheet or tabular business data that does not match "
        "a more specific document type"
    ),

    "presentation": (
        "A presentation or slide deck containing slide-based content"
    ),

    "unknown": (
        "Use when the document cannot be confidently classified into "
        "any of the available document types"
    ),
}


def _build_type_descriptions_block() -> str:
    """
    Build the ALLOWED TYPES section dynamically from DOCUMENT_TYPES.

    This ensures that the prompt stays synchronized with the application's
    actual document type registry.
    """

    lines = []

    for doc_type in DOCUMENT_TYPES.keys():

        description = TYPE_DESCRIPTIONS.get(doc_type, "")

        if description:
            lines.append(
                f"- {doc_type}: {description}"
            )
        else:
            lines.append(
                f"- {doc_type}"
            )

    return "\n".join(lines)


# ============================================================================
# TEXT UTILITIES
# ============================================================================

def _limit_words(text: str, max_words: int = MAX_PREVIEW_WORDS) -> str:
    """
    Limit text to a maximum number of words.

    This is preferable to slicing characters because classification quality
    depends more naturally on the amount of semantic content than raw
    character count.
    """

    if not text:
        return ""

    words = text.split()

    if len(words) <= max_words:
        return text

    return " ".join(words[:max_words])


def _clean_text(text: str) -> str:
    """
    Perform lightweight cleanup.

    We intentionally do NOT perform aggressive normalization because
    document classification can depend on:

        - headings
        - numbers
        - financial terminology
        - section names
        - dates
        - table-like structures
    """

    if not text:
        return ""

    # Normalize line endings.
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Remove excessive blank lines.
    lines = []

    previous_blank = False

    for line in text.split("\n"):

        line = line.strip()

        if not line:
            if not previous_blank:
                lines.append("")
            previous_blank = True
            continue

        lines.append(line)
        previous_blank = False

    return "\n".join(lines).strip()


def _word_count(text: str) -> int:
    """Return approximate word count."""

    if not text:
        return 0

    return len(text.split())


# ============================================================================
# PDF EXTRACTION
# ============================================================================

def _extract_pdf_preview(
    content: bytes,
    max_words: int = MAX_PREVIEW_WORDS,
) -> str:
    """
    Extract a representative text preview from a PDF.

    Strategy:

    Phase 1
    -------
    Extract the first INITIAL_PDF_PAGES pages.

    Phase 2
    -------
    If the first pages do not contain enough text, inspect additional
    sampled pages.

    Phase 3
    -------
    For long documents, include representative pages from:

        - beginning
        - early-middle
        - middle
        - late-middle
        - end

    This gives the classifier information about the document structure
    without parsing the entire PDF.

    IMPORTANT:
    This is only a CHEAP preview. The real parsing/OCR pipeline should
    handle full-document extraction.
    """

    try:
        import fitz  # PyMuPDF

        doc = fitz.open(
            stream=content,
            filetype="pdf",
        )

        page_count = doc.page_count

        if page_count == 0:
            doc.close()
            return ""

        # ---------------------------------------------------------------
        # Determine pages to inspect.
        # ---------------------------------------------------------------

        pages_to_read = []

        # First pages are usually the most informative.
        first_pages = min(
            INITIAL_PDF_PAGES,
            page_count,
        )

        pages_to_read.extend(
            range(first_pages)
        )

        # ---------------------------------------------------------------
        # If the document is longer, sample representative pages.
        # ---------------------------------------------------------------

        if page_count > first_pages:

            # Generate evenly distributed page positions.
            sample_count = min(
                7,
                MAX_PDF_PAGES_TO_INSPECT - len(pages_to_read),
            )

            if sample_count > 0:

                for i in range(sample_count):

                    position = int(
                        (i + 1)
                        * (page_count - 1)
                        / (sample_count + 1)
                    )

                    pages_to_read.append(position)

        # Remove duplicates and sort.
        pages_to_read = sorted(
            set(pages_to_read)
        )

        # Safety limit.
        pages_to_read = pages_to_read[
            :MAX_PDF_PAGES_TO_INSPECT
        ]

        # ---------------------------------------------------------------
        # Extract selected pages.
        # ---------------------------------------------------------------

        page_texts = []

        total_words = 0

        for page_number in pages_to_read:

            try:
                page = doc.load_page(page_number)

                text = page.get_text("text")

                if not text:
                    continue

                text = _clean_text(text)

                if not text:
                    continue

                # Limit one page so that a single dense page cannot
                # dominate the entire classification prompt.
                text = text[:MAX_CHARS_PER_PAGE]

                words = _word_count(text)

                if words == 0:
                    continue

                page_texts.append(
                    f"[PAGE {page_number + 1}]\n{text}"
                )

                total_words += words

                # If we already have enough material, stop early.
                if total_words >= max_words:
                    break

            except Exception as exc:
                logger.warning(
                    "pdf_page_preview_failed",
                    page=page_number + 1,
                    error=str(exc),
                )

        doc.close()

        if not page_texts:
            return ""

        combined = "\n\n".join(page_texts)

        return _limit_words(
            combined,
            max_words,
        )

    except Exception as exc:

        logger.warning(
            "pdf_preview_extraction_failed",
            error=str(exc),
        )

        return ""


# ============================================================================
# DOCX EXTRACTION
# ============================================================================

def _extract_docx_preview(
    content: bytes,
    max_words: int = MAX_PREVIEW_WORDS,
) -> str:
    """
    Extract a lightweight preview from a DOCX file.

    Paragraphs are preferred because they preserve the document's
    semantic structure better than raw XML extraction.
    """

    try:

        from docx import Document as DocxDocument

        doc = DocxDocument(
            io.BytesIO(content)
        )

        parts = []

        for paragraph in doc.paragraphs:

            text = paragraph.text.strip()

            if text:
                parts.append(text)

            # Stop collecting if we already have plenty of text.
            if _word_count("\n".join(parts)) >= max_words:
                break

        text = "\n".join(parts)

        return _limit_words(
            _clean_text(text),
            max_words,
        )

    except Exception as exc:

        logger.warning(
            "docx_preview_extraction_failed",
            error=str(exc),
        )

        return ""


# ============================================================================
# TXT / MARKDOWN EXTRACTION
# ============================================================================

def _extract_text_preview(
    content: bytes,
    max_words: int = MAX_PREVIEW_WORDS,
) -> str:
    """
    Extract preview from TXT or Markdown.

    UTF-8 is preferred, with a fallback for common Windows text files.
    """

    try:

        try:
            text = content.decode(
                "utf-8"
            )

        except UnicodeDecodeError:

            text = content.decode(
                "cp1252",
                errors="ignore",
            )

        return _limit_words(
            _clean_text(text),
            max_words,
        )

    except Exception as exc:

        logger.warning(
            "text_preview_extraction_failed",
            error=str(exc),
        )

        return ""


# ============================================================================
# MAIN CLASSIFIER
# ============================================================================

class AIBasedClassifier(BaseClassifier):
    """
    Ollama-powered document classifier.

    The classifier supports two modes:

    1. classify()
       ------------------------------------------------
       Used during upload/pre-processing.

       It receives:

           filename
           mime_type
           raw bytes

       It creates a CHEAP representative preview.

    2. classify_text()
       ------------------------------------------------
       Used after parsing.

       It receives already extracted document text and can therefore
       classify using much richer information.
    """

    def __init__(self, model=MODEL):

        self.model = model

        self._system_prompt = SYSTEM_PROMPT.format(
            type_descriptions=_build_type_descriptions_block()
        )

    # ------------------------------------------------------------------------
    # FULL TEXT CLASSIFICATION
    # ------------------------------------------------------------------------

    async def classify_text(
        self,
        text: str,
    ) -> ClassificationResult:
        """
        Classify already extracted document text.

        This is the preferred classification method after parsing.

        The input is bounded to MAX_PREVIEW_WORDS so that accidentally
        passing a 200-page document does not create an enormous Ollama
        request.
        """

        # Clean and limit text.
        text = _clean_text(text)

        text = _limit_words(
            text,
            MAX_PREVIEW_WORDS,
        )

        if not text:

            logger.warning(
                "ai_classification_empty_text"
            )

            return ClassificationResult(
                document_type="unknown",
                confidence=0.0,
                method="ai_based",
                model_version=self.model,
            )

        user_prompt = USER_PROMPT_TEMPLATE.format(
            text=text
        )

        try:

            # ---------------------------------------------------------------
            # Ollama normally does not require Authorization for local use.
            #
            # The old implementation used:
            #
            #     Authorization: Bearer {OLLAMA_URL}
            #
            # which is not a valid authentication scheme.
            #
            # Keep headers empty unless your deployment explicitly requires
            # authentication.
            # ---------------------------------------------------------------

            headers = {}

            async with httpx.AsyncClient(
                timeout=OLLAMA_TIMEOUT_SECONDS,
                headers=headers,
            ) as client:

                response = await client.post(
                    f"{settings.OLLAMA_URL}/api/generate",

                    json={
                        "model": self.model,

                        "system": self._system_prompt,

                        "prompt": user_prompt,

                        "stream": False,

                        # Ask Ollama for JSON.
                        "format": "json",

                        # Deterministic classification.
                        "options": {
                            "temperature": 0,
                        },
                    },
                )

                response.raise_for_status()

                raw = response.json().get(
                    "response",
                    "{}",
                )

                # -----------------------------------------------------------
                # Parse model JSON.
                # -----------------------------------------------------------

                parsed = json.loads(raw)

                doc_type = parsed.get(
                    "type",
                    "unknown",
                )

                # -----------------------------------------------------------
                # Validate document type.
                # -----------------------------------------------------------

                if doc_type not in DOCUMENT_TYPES:

                    logger.warning(
                        "ai_classification_invalid_type",
                        returned_type=doc_type,
                    )

                    doc_type = "unknown"

                # -----------------------------------------------------------
                # Validate confidence.
                # -----------------------------------------------------------

                try:

                    confidence = float(
                        parsed.get(
                            "confidence",
                            0.5,
                        )
                    )

                except (
                    TypeError,
                    ValueError,
                ):

                    confidence = 0.5

                # Keep confidence inside [0, 1].
                confidence = max(
                    0.0,
                    min(
                        1.0,
                        confidence,
                    ),
                )

                logger.info(
                    "ai_classification_completed",
                    document_type=doc_type,
                    confidence=confidence,
                    model=self.model,
                    preview_words=_word_count(text),
                )

                return ClassificationResult(
                    document_type=doc_type,
                    confidence=confidence,
                    method="ai_based",
                    model_version=self.model,
                )

        except json.JSONDecodeError as exc:

            logger.error(
                "ai_classification_invalid_json",
                error=str(exc),
                raw_response=raw[:500] if "raw" in locals() else "",
            )

            return ClassificationResult(
                document_type="unknown",
                confidence=0.0,
                method="ai_based",
                model_version=self.model,
            )

        except httpx.HTTPError as exc:

            logger.error(
                "ai_classification_ollama_http_error",
                error=str(exc),
            )

            return ClassificationResult(
                document_type="unknown",
                confidence=0.0,
                method="ai_based",
                model_version=self.model,
            )

        except Exception as exc:

            logger.error(
                "ai_classification_failed",
                error=str(exc),
            )

            return ClassificationResult(
                document_type="unknown",
                confidence=0.0,
                method="ai_based",
                model_version=self.model,
            )

    # ------------------------------------------------------------------------
    # PRE-PARSE CLASSIFICATION
    # ------------------------------------------------------------------------

    async def classify(
        self,
        filename: str,
        mime_type: str,
        content: bytes,
    ) -> ClassificationResult:
        """
        Perform lightweight classification before the full parsing stage.

        Instead of classifying only from the filename or only from page 1,
        this method generates a representative preview.

        Example for a 200-page 10-K:

            pages 1-5
            +
            representative pages
            +
            filename
            ↓
            up to 3000 words
            ↓
            Ollama
        """

        preview_text = self._cheap_text_preview(
            filename=filename,
            mime_type=mime_type,
            content=content,
            max_words=MAX_PREVIEW_WORDS,
        )

        # Always include the filename because filenames often contain
        # useful information such as:
        #
        #     annual_report.pdf
        #     invoice_2026_001.pdf
        #     bank_statement_january.pdf
        #
        combined = (
            f"Filename: {filename}\n\n"
            f"{preview_text}"
            if preview_text
            else f"Filename: {filename}"
        )

        return await self.classify_text(
            combined
        )

    # ------------------------------------------------------------------------
    # CHEAP PREVIEW
    # ------------------------------------------------------------------------

    def _cheap_text_preview(
        self,
        filename: str,
        mime_type: str,
        content: bytes,
        max_words: int = MAX_PREVIEW_WORDS,
    ) -> str:
        """
        Generate representative text without running the full parser.

        Supported:

            PDF
            TXT
            Markdown
            DOCX

        For PDFs, this now uses multiple pages instead of only page 1.
        """

        try:

            lower_filename = filename.lower()

            # ================================================================
            # TXT / MARKDOWN
            # ================================================================

            if (
                mime_type == "text/plain"
                or lower_filename.endswith(
                    (".txt", ".md")
                )
            ):

                return _extract_text_preview(
                    content,
                    max_words,
                )

            # ================================================================
            # PDF
            # ================================================================

            if (
                mime_type == "application/pdf"
                or lower_filename.endswith(".pdf")
            ):

                return _extract_pdf_preview(
                    content,
                    max_words,
                )

            # ================================================================
            # DOCX
            # ================================================================

            if (
                mime_type
                == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                or lower_filename.endswith(".docx")
            ):

                return _extract_docx_preview(
                    content,
                    max_words,
                )

        except Exception as exc:

            logger.warning(
                "cheap_text_preview_failed",
                filename=filename,
                error=str(exc),
            )

        return ""