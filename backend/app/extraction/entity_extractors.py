
# ===== app/extraction/entity_extractors.py =====
"""
Rule-based NER via regex — pragmatic and dependency-light, consistent with
Phase 8's metadata approach. AIEntityExtractor (Ollama) below is the upgrade
path for free-text entities (person names, addresses) regex handles poorly.
"""
import re
from app.canonical.schema import CanonicalDocument
from app.extraction.schema import ExtractedEntity

PATTERNS = {
    "invoice_number": r"(?:invoice\s*(?:no|#|number)?[:\s]+)([A-Z0-9\-\/]{3,20})",
    "po_number": r"(?:p\.?o\.?\s*(?:no|#|number)?[:\s]+)([A-Z0-9\-\/]{3,20})",
    "receipt_number": r"(?:receipt\s*(?:no|#|number)?[:\s]+)([A-Z0-9\-\/]{3,20})",
    "tax_id": r"(?:tax\s*id[:\s]+)([A-Z0-9\-]{5,20})",
    "vat_number": r"(?:vat\s*(?:no|#|number)?[:\s]+)([A-Z0-9\-]{5,20})",
    "bank_account": r"(?:account\s*(?:no|#|number)?[:\s]+)(\d{6,20})",
    "postal_code": r"\b(\d{5}(?:-\d{4})?)\b",
    "email": r"\b([\w.+-]+@[\w-]+\.[\w.-]+)\b",
    "phone": r"\b(\+?\d{1,3}[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4})\b",
}

class RegexEntityExtractor:
    method = "rule_based"

    def extract(self, doc: CanonicalDocument) -> list[ExtractedEntity]:
        entities = []
        for block in doc.blocks:
            for entity_type, pattern in PATTERNS.items():
                for match in re.finditer(pattern, block.text, re.IGNORECASE):
                    entities.append(ExtractedEntity(
                        entity_type=entity_type, value=match.group(1).strip(),
                        confidence=0.7, page=block.page, block_id=block.block_id,
                        bbox=block.bbox.model_dump() if block.bbox else None, method=self.method,
                    ))
        return entities