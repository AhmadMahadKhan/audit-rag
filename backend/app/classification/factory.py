from app.classification.rule_based import RuleBasedClassifier
from app.classification.ai_based import AIBasedClassifier
from app.classification.hybrid import HybridClassifier
from app.classification.base import BaseClassifier
from app.core.config import settings

def get_classifier() -> BaseClassifier:
    method = settings.CLASSIFICATION_METHOD
    if method == "rule_based":
        return RuleBasedClassifier()
    if method == "ai_based":
        return AIBasedClassifier()
    if method == "hybrid":
        return HybridClassifier()
    raise ValueError(f"Unknown classification method: {method}")