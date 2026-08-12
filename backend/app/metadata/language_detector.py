# ===== app/metadata/language_detector.py =====
from langdetect import detect, DetectorFactory, LangDetectException
from app.metadata.base import BaseExtractor
from app.metadata.schema import MetadataField
from app.canonical.schema import CanonicalDocument

DetectorFactory.seed = 0  # deterministic results

class LanguageDetector(BaseExtractor):
    name = "language_detector"

    def extract(self, doc: CanonicalDocument) -> list[MetadataField]:
        text = doc.raw_text[:2000].strip()
        if not text:
            return []
        try:
            lang = detect(text)
            confidence = 0.85  # langdetect doesn't expose a real score; conservative flat estimate
        except LangDetectException:
            return []
        return [MetadataField(key="language", value=lang, category="document", confidence=confidence, extractor=self.name)]
