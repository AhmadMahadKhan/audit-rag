# ===== app/reranking/jina_provider.py =====
"""Optional cloud reranker — requires JINA_API_KEY. Kept minimal per local-first default."""
import httpx
from app.reranking.base import BaseReranker
from app.core.config import settings

class JinaReranker(BaseReranker):
    name = "jina"

    def __init__(self, model: str = "jina-reranker-v2-base-multilingual"):
        self.model = model
        self.model_version = model
        if not getattr(settings, "JINA_API_KEY", None):
            raise ValueError("JINA_API_KEY not configured")

    async def score(self, query: str, documents: list[str]) -> list[float]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post("https://api.jina.ai/v1/rerank",
                headers={"Authorization": f"Bearer {settings.JINA_API_KEY}"},
                json={"model": self.model, "query": query, "documents": documents})
            resp.raise_for_status()
            results = sorted(resp.json()["results"], key=lambda r: r["index"])
            return [r["relevance_score"] for r in results]
