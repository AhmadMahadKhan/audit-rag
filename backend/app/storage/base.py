from abc import ABC, abstractmethod

class BaseStorageBackend(ABC):
    @abstractmethod
    async def save(self, path: str, content: bytes) -> str:
        pass

    @abstractmethod
    async def read(self, path: str) -> bytes:
        pass

    @abstractmethod
    async def delete(self, path: str) -> bool:
        pass
