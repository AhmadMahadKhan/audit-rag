# ===== app/metadata/currency_extractor.py =====
import re
from app.metadata.base import BaseExtractor
from app.metadata.schema import MetadataField
from app.canonical.schema import CanonicalDocument

CURRENCY_SYMBOLS = {"$": "USD", "€": "EUR", "£": "GBP", "₹": "INR", "¥": "JPY", "₨": "PKR"}
ISO_CODE_PATTERN = re.compile(r"\b(USD|EUR|GBP|PKR|INR|JPY|AED|CAD|AUD)\b")

class CurrencyExtractor(BaseExtractor):
    name = "currency_extractor"

    def extract(self, doc: CanonicalDocument) -> list[MetadataField]:
        text = doc.raw_text
        iso_match = ISO_CODE_PATTERN.search(text)
        if iso_match:
            return [MetadataField(key="currency", value=iso_match.group(1), category="financial", confidence=0.9, extractor=self.name)]

        for symbol, code in CURRENCY_SYMBOLS.items():
            if symbol in text:
                return [MetadataField(key="currency", value=code, category="financial", confidence=0.6, extractor=self.name)]
        return []