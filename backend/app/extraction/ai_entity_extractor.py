# ===== app/extraction/ai_entity_extractor.py =====
"""AI-based extractor for entities regex can't reliably find: person names,
organizations, addresses. Uses Ollama with JSON-constrained output."""
import json
import httpx
from app.canonical.schema import CanonicalDocument
from app.extraction.schema import ExtractedEntity
from app.core.config import settings
from app.core.logging_config import logger

PROMPT = """Extract named entities from this text. Return ONLY JSON array of
objects with keys "type" (one of: organization, person, address, department)
and "value". Text:

{text}"""

class AIEntityExtractor:
    method = "ai_based"

    def __init__(self, model: str = "llama3.1"):
        self.model = model

    async def extract(self, doc: CanonicalDocument) -> list[ExtractedEntity]:
        text = doc.raw_text[:3000]
        if not text.strip():
            return []
        try:
            headers = {"Authorization": f"Bearer {settings.OLLAMA_API_KEY}"} if settings.OLLAMA_API_KEY else {}
            async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
                resp = await client.post(f"{settings.OLLAMA_URL}/api/generate", json={
                    "model": self.model, "prompt": PROMPT.format(text=text), "stream": False, "format": "json",
                })
                resp.raise_for_status()
                raw = resp.json().get("response", "[]")
                items = json.loads(raw)
                if not isinstance(items, list):
                    items = items.get("entities", [])
                return [
                    ExtractedEntity(entity_type=i["type"], value=i["value"], confidence=0.6, method=self.method)
                    for i in items if i.get("type") and i.get("value")
                ]
        except Exception as e:
            logger.error("ai_entity_extraction_failed", error=str(e))
            return []
