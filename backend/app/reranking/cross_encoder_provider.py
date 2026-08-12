# ===== app/reranking/cross_encoder_provider.py =====
"""Default: sentence-transformers CrossEncoder (BGE-reranker-compatible interface,
runs locally, no external API — consistent with local-first Ollama stack)."""
import asyncio
from app.reranking.base import BaseReranker
from app.core.config import settings

class CrossEncoderReranker(BaseReranker):
    name = "sentence_transformers"

    def __init__(self, model_name: str = None):
        from sentence_transformers import CrossEncoder
        self.model_name = model_name or settings.RERANKER_MODEL
        self.model_version = self.model_name
        self._model = CrossEncoder(self.model_name)

    async def score(self, query: str, documents: list[str]) -> list[float]:
        loop = asyncio.get_event_loop()
        pairs = [[query, doc] for doc in documents]
        scores = await loop.run_in_executor(None, lambda: self._model.predict(pairs).tolist())
        return scores
