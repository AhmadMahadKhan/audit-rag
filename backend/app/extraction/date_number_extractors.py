
# ===== app/extraction/date_number_extractors.py =====
import re
from dateutil import parser as date_parser
from app.canonical.schema import CanonicalDocument
from app.extraction.schema import ExtractedEntity

DATE_LABELS = {
    "invoice_date": r"invoice\s*date[:\s]+", "due_date": r"due\s*date[:\s]+",
    "payment_date": r"payment\s*date[:\s]+", "contract_date": r"contract\s*date[:\s]+",
}
GENERIC_DATE = r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2})"

class DateEntityExtractor:
    method = "rule_based"

    def extract(self, doc: CanonicalDocument) -> list[ExtractedEntity]:
        entities = []
        for key, label in DATE_LABELS.items():
            match = re.search(label + GENERIC_DATE, doc.raw_text, re.IGNORECASE)
            if match:
                try:
                    normalized = date_parser.parse(match.group(1), fuzzy=True).date().isoformat()
                    entities.append(ExtractedEntity(entity_type=key, value=normalized, confidence=0.75, method=self.method))
                except Exception:
                    pass
        return entities
