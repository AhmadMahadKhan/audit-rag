import os
import aiofiles
from app.storage.base import BaseStorageBackend
from app.core.config import settings

class LocalStorageBackend(BaseStorageBackend):
    def __init__(self, base_dir: str | None = None):
        self.base_dir = base_dir or settings.STORAGE_LOCAL_PATH
        self.base_path = self.base_dir

    def _full_path(self, path: str) -> str:
        return os.path.join(self.base_dir, path)

    async def save(self, path: str, content: bytes) -> str:
        full_path = self._full_path(path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        async with aiofiles.open(full_path, "wb") as f:
            await f.write(content)
        return full_path

    async def read(self, path: str) -> bytes:
        full_path = self._full_path(path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {path}")
        async with aiofiles.open(full_path, "rb") as f:
            return await f.read()

    async def delete(self, path: str) -> bool:
        full_path = self._full_path(path)
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
        return False
