
# ===== app/embeddings/ollama_provider.py =====
import httpx
from app.embeddings.base import BaseEmbeddingProvider
from app.core.config import settings
from app.core.logging_config import logger

class OllamaEmbeddingProvider(BaseEmbeddingProvider):
    name = "ollama"

    def __init__(self, model: str = None):
        self.model = model or settings.EMBEDDING_MODEL
        self.model_version = self.model
        self.dimension = settings.EMBEDDING_DIMENSION

    async def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = []
        async with httpx.AsyncClient(timeout=60.0) as client:
            for text in texts:
                try:
                    resp = await client.post(f"{settings.OLLAMA_URL}/api/embeddings",
                                               json={"model": self.model, "prompt": text})
                    resp.raise_for_status()
                    vec = resp.json().get("embedding", [])
                    vectors.append(vec)
                except Exception as e:
                    logger.error("ollama_embedding_failed", error=str(e))
                    vectors.append([])
        return vectors
