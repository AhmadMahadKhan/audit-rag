
# ===== app/vectorstore/base.py =====
from abc import ABC, abstractmethod

class VectorStoreProvider(ABC):
    @abstractmethod
    async def ensure_collection(self, name: str, dimension: int): ...

    @abstractmethod
    async def upsert(self, collection: str, points: list[dict]): ...

    @abstractmethod
    async def search(self, collection: str, vector: list[float], top_k: int, filters: dict | None = None) -> list[dict]: ...

    @abstractmethod
    async def delete(self, collection: str, point_ids: list[str]): ...

    @abstractmethod
    async def get_collection_stats(self, collection: str) -> dict: ...

    @abstractmethod
    async def list_collections(self) -> list[str]: ...

    @abstractmethod
    async def delete_collection(self, name: str): ...