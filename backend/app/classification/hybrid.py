from app.classification.base import BaseClassifier, ClassificationResult
from app.classification.rule_based import RuleBasedClassifier
from app.classification.ai_based import AIBasedClassifier
from app.core.config import settings

class HybridClassifier(BaseClassifier):
    """Rule-based first (cheap); falls through to AI only when confidence is low."""
    def __init__(self):
        self.rule_classifier = RuleBasedClassifier()
        self.ai_classifier = AIBasedClassifier()

    async def classify(self, filename: str, mime_type: str, content: bytes) -> ClassificationResult:
        result = await self.rule_classifier.classify(filename, mime_type, content)
        if result.confidence >= settings.CLASSIFICATION_CONFIDENCE_THRESHOLD:
            return result
        ai_result = await self.ai_classifier.classify(filename, mime_type, content)
        return ai_result if ai_result.confidence > result.confidence else result