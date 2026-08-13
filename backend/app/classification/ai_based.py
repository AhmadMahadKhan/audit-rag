"""
Text-content classification via Ollama. Needs extracted text.
"""
import json
import httpx
from app.classification.base import BaseClassifier, ClassificationResult
from app.classification.document_types import DOCUMENT_TYPES
from app.core.config import settings
from app.core.logging_config import logger

PROMPT_TEMPLATE = """Classify this document into exactly one type from: {types}.
Respond ONLY with JSON: {{"type": "...", "confidence": 0.0-1.0}}

Document excerpt:
{text}"""

class AIBasedClassifier(BaseClassifier):
    def __init__(self, model: str = "llama3.1"):
        self.model = model

    async def classify_text(self, text: str) -> ClassificationResult:
        prompt = PROMPT_TEMPLATE.format(types=", ".join(DOCUMENT_TYPES.keys()), text=text[:2000])
        try:
            headers = {"Authorization": f"Bearer {settings.OLLAMA_API_KEY}"} if settings.OLLAMA_API_KEY else {}
            async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
                resp = await client.post(
                    f"{settings.OLLAMA_URL}/api/generate",
                    json={"model": self.model, "prompt": prompt, "stream": False, "format": "json"},
                )
                resp.raise_for_status()
                raw = resp.json().get("response", "{}")
                parsed = json.loads(raw)
                doc_type = parsed.get("type", "unknown")
                if doc_type not in DOCUMENT_TYPES:
                    doc_type = "unknown"
                return ClassificationResult(
                    document_type=doc_type, confidence=float(parsed.get("confidence", 0.5)),
                    method="ai_based", model_version=self.model,
                )
        except Exception as e:
            logger.error("ai_classification_failed", error=str(e))
            return ClassificationResult(document_type="unknown", confidence=0.0, method="ai_based", model_version=self.model)

    async def classify(self, filename: str, mime_type: str, content: bytes) -> ClassificationResult:
        # No parsed text available yet (pre-Phase 6) — fall back to filename as weak signal
        return await self.classify_text(filename)
