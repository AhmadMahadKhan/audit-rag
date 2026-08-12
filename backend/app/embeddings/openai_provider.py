
# ===== app/embeddings/openai_provider.py =====
"""Optional cloud provider — requires OPENAI_API_KEY. Stub kept minimal since
local-first (Ollama) is the stated default."""
import httpx
from app.embeddings.base import BaseEmbeddingProvider
from app.core.config import settings

class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    name = "openai"

    def __init__(self, model: str = "text-embedding-3-small"):
        self.model = model
        self.model_version = model
        self.dimension = 1536
        if not getattr(settings, "OPENAI_API_KEY", None):
            raise ValueError("OPENAI_API_KEY not configured")

    async def embed(self, texts: list[str]) -> list[list[float]]:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                json={"model": self.model, "input": texts},
            )
            resp.raise_for_status()
            data = resp.json()["data"]
            return [d["embedding"] for d in sorted(data, key=lambda x: x["index"])]
