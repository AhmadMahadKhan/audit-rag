# ===== app/chunking/financial_statement_chunker.py =====
from app.chunking.base import BaseChunker
from app.chunking.schema import ChunkCandidate
from app.chunking.table_chunker import TableChunker
from app.chunking.token_utils import estimate_tokens
from app.canonical.schema import CanonicalDocument

# Blocks whose text matches these (case-insensitive substring) are treated as


NARRATIVE_SECTION_KEYWORDS = [
    "management's discussion", "md&a", "notes to financial statements",
    "report of independent", "auditor's report", "risk factors",
    "critical accounting", "liquidity and capital resources",
]


class FinancialStatementChunker(BaseChunker):
    """Table-aware chunker for financial_statement, bank_statement,
    tax_document, and audit_report types. Tables are chunked via
    TableChunker (row-batched, header-preserved). Narrative text is
    chunked token-window style, bounded by max_tokens, so a single
    MD&A/notes section can't produce one oversized chunk."""

    name = "financial_statement_chunker"

    def chunk(self, doc: CanonicalDocument) -> list[ChunkCandidate]:
        candidates = []

        # --- Tables: delegate entirely to TableChunker ---
        table_chunker = TableChunker()
        for table in doc.tables:
            candidates.extend(table_chunker.chunk_table(doc.info.document_id, table))

        # --- Narrative text: token-windowed, heading-bounded (GenericChunker-style) ---
        candidates.extend(self._chunk_narrative(doc))

        return candidates

    def _chunk_narrative(self, doc: CanonicalDocument) -> list[ChunkCandidate]:
        candidates = []
        buffer_text, buffer_pages, buffer_blocks = [], set(), []
        current_heading = None
        token_total = 0

        def flush():
            if buffer_text:
                candidates.append(ChunkCandidate(
                    chunk_type="narrative",
                    content="\n".join(buffer_text),
                    section_name=current_heading,
                    pages=sorted(buffer_pages),
                    block_ids=list(buffer_blocks),
                    heading_path=[current_heading] if current_heading else [],
                ))

        for block in sorted(doc.blocks, key=lambda b: (b.page, b.order)):
            text_lower = block.text.lower()

            is_section_heading = (
                block.type == "heading"
                or any(kw in text_lower for kw in NARRATIVE_SECTION_KEYWORDS)
            )

            if is_section_heading:
                flush()
                buffer_text, buffer_pages, buffer_blocks = [], set(), []
                token_total = 0
                current_heading = block.text

            block_tokens = estimate_tokens(block.text)
            if token_total + block_tokens > self.max_tokens and buffer_text:
                flush()
                overlap_text = buffer_text[-1] if buffer_text else ""
                buffer_text = [overlap_text] if overlap_text else []
                buffer_pages, buffer_blocks = set(), []
                token_total = estimate_tokens(overlap_text)

            buffer_text.append(block.text)
            buffer_pages.add(block.page)
            buffer_blocks.append(block.block_id)
            token_total += block_tokens

        flush()
        return candidates