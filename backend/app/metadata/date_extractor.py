# ===== app/metadata/date_extractor.py =====
import re
from dateutil import parser as date_parser
from app.metadata.base import BaseExtractor
from app.metadata.schema import MetadataField
from app.canonical.schema import CanonicalDocument

DATE_PATTERN = re.compile(
    r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2}|"
    r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4})\b",
    re.IGNORECASE,
)

DATE_LABEL_HINTS = {
    "invoice_date": r"invoice\s*date[:\s]", "due_date": r"due\s*date[:\s]",
    "effective_date": r"effective\s*date[:\s]", "expiration_date": r"expir\w*\s*date[:\s]",
}

class DateExtractor(BaseExtractor):
    name = "date_extractor"

    def extract(self, doc: CanonicalDocument) -> list[MetadataField]:
        text = doc.raw_text
        fields = []

        for key, label_pattern in DATE_LABEL_HINTS.items():
            match = re.search(label_pattern + r"\s*(" + DATE_PATTERN.pattern + r")", text, re.IGNORECASE)
            if match:
                normalized = self._normalize(match.group(1))
                if normalized:
                    fields.append(MetadataField(key=key, value=normalized, category="business", confidence=0.8, extractor=self.name))

        if not fields:
            generic = DATE_PATTERN.findall(text)
            if generic:
                normalized = self._normalize(generic[0])
                if normalized:
                    fields.append(MetadataField(key="document_date", value=normalized, category="business", confidence=0.5, extractor=self.name))
        return fields

    def _normalize(self, raw: str) -> str | None:
        try:
            return date_parser.parse(raw, fuzzy=True).date().isoformat()
        except Exception:
            return None
