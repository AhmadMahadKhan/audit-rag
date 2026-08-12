
# ===== app/metadata/company_extractor.py =====
"""
Rule-based company/vendor/customer extraction from labeled lines. Real NER
(spaCy/AI) is a stronger approach — flagged as future work; this covers the
common "Vendor: X" / "Bill To: X" document convention without external deps.
"""
import re
from app.metadata.base import BaseExtractor
from app.metadata.schema import MetadataField
from app.canonical.schema import CanonicalDocument

LABEL_PATTERNS = {
    "vendor": r"(?:vendor|from|seller)[:\s]+([A-Z][A-Za-z0-9&.,\s]{2,50})(?:\n|$)",
    "customer": r"(?:bill\s*to|customer|client)[:\s]+([A-Z][A-Za-z0-9&.,\s]{2,50})(?:\n|$)",
    "company": r"(?:company)[:\s]+([A-Z][A-Za-z0-9&.,\s]{2,50})(?:\n|$)",
}

class CompanyExtractor(BaseExtractor):
    name = "company_extractor"

    def extract(self, doc: CanonicalDocument) -> list[MetadataField]:
        text = doc.raw_text
        fields = []
        for key, pattern in LABEL_PATTERNS.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip().rstrip(",.")
                if value:
                    fields.append(MetadataField(key=key, value=value, category="business", confidence=0.65, extractor=self.name))
        return fields