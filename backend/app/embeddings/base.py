
# ===== app/embeddings/base.py =====
from abc import ABC, abstractmethod

class BaseEmbeddingProvider(ABC):
    name: str = "base"
    model_version: str = "1.0"
    dimension: int = 0

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]: ...
