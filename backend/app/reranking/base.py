# ===== app/reranking/base.py =====
from abc import ABC, abstractmethod

class BaseReranker(ABC):
    name: str = "base"
    model_version: str = "1.0"

    @abstractmethod
    async def score(self, query: str, documents: list[str]) -> list[float]: ...
