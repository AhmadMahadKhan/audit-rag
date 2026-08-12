
# ===== app/extraction/fact_extractor.py =====
"""Derives business facts from extracted entities + raw text financial figures."""
import re
from app.canonical.schema import CanonicalDocument
from app.extraction.schema import ExtractedFact


MONEY_LABELS = {
    "invoice_total": r"\btotal[:\s]+\$?([\d,]+\.?\d*)",  # \b prevents matching inside "Subtotal"
    "subtotal": r"sub\s*-?\s*total[:\s]+\$?([\d,]+\.?\d*)",
    "tax_amount": r"tax(?:\s*amount)?[:\s]+\$?([\d,]+\.?\d*)",
    "discount": r"discount[:\s]+\$?([\d,]+\.?\d*)",
}

class FinancialFactExtractor:
    def extract(self, doc: CanonicalDocument) -> list[ExtractedFact]:
        facts = []
        for fact_type, pattern in MONEY_LABELS.items():
            match = re.search(pattern, doc.raw_text, re.IGNORECASE)
            if match:
                raw_value = match.group(1).replace(",", "")
                try:
                    numeric = float(raw_value)
                    facts.append(ExtractedFact(fact_type=fact_type, value=raw_value, numeric_value=numeric, confidence=0.75))
                except ValueError:
                    pass
        return facts