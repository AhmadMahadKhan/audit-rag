
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
        self._fallback_provider = None

    def _get_fallback(self):
        if self._fallback_provider is None:
            from app.embeddings.sentence_transformers_provider import SentenceTransformersProvider
            self._fallback_provider = SentenceTransformersProvider()
        return self._fallback_provider

    async def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = []
        headers = {"Authorization": f"Bearer {settings.OLLAMA_URL}"} if settings.OLLAMA_URL else {}
        async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
            for text in texts:
                try:
                    resp = await client.post(f"{settings.OLLAMA_URL}/api/embed",
                                               json={"model": self.model, "input": text})
                    resp.raise_for_status()
                    data = resp.json()
                    embeddings = data.get("embeddings", [])
                    vec = embeddings[0] if embeddings else data.get("embedding", [])
                    if vec:
                        vectors.append(vec)
                    else:
                        raise ValueError("Empty embedding vector returned")
                except Exception as e:
                    logger.warning("ollama_embedding_failed_using_sentence_transformers_fallback", error=str(e))
                    try:
                        fallback_vecs = await self._get_fallback().embed([text])
                        vectors.append(fallback_vecs[0])
                    except Exception as fallback_err:
                        logger.error("sentence_transformers_fallback_failed", error=str(fallback_err))
                        import hashlib
                        h = hashlib.sha256(text.encode()).digest()
                        pseudo_vec = [(b / 255.0 * 2.0 - 1.0) for b in (h * 24)[:self.dimension]]
                        vectors.append(pseudo_vec)
        return vectors
