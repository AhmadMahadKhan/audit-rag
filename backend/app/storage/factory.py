from app.storage.base import BaseStorageBackend
from app.storage.local import LocalStorageBackend
from app.core.config import settings

def get_storage_backend(provider: str | None = None) -> BaseStorageBackend:
    provider_name = provider or settings.STORAGE_PROVIDER
    if provider_name == "local":
        return LocalStorageBackend()
    raise ValueError(f"Unsupported storage provider: {provider_name}")
