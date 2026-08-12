
# ===== app/embeddings/sentence_transformers_provider.py =====
"""Local CPU/GPU alternative — no network dependency on Ollama being up."""
from app.embeddings.base import BaseEmbeddingProvider

class SentenceTransformersProvider(BaseEmbeddingProvider):
    name = "sentence_transformers"

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        from sentence_transformers import SentenceTransformer
        self._model = SentenceTransformer(model_name)
        self.model_version = model_name
        self.dimension = self._model.get_sentence_embedding_dimension()

    async def embed(self, texts: list[str]) -> list[list[float]]:
        import asyncio
        loop = asyncio.get_event_loop()
        vectors = await loop.run_in_executor(None, lambda: self._model.encode(texts, normalize_embeddings=True).tolist())
        return vectors