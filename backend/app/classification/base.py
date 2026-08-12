# ===== app/classification/base.py =====
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class ClassificationResult:
    document_type: str
    confidence: float
    method: str
    model_version: str | None = None

class BaseClassifier(ABC):
    @abstractmethod
    async def classify(self, filename: str, mime_type: str, content: bytes) -> ClassificationResult: ...
