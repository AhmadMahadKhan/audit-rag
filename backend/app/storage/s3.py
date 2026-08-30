# ===== app/storage/s3.py =====
"""S3-compatible backend stub — implement when needed (boto3 + async wrapper or aioboto3)."""
from app.storage.base import StorageBackend

class S3Storage(StorageBackend):
    def __init__(self, bucket: str, endpoint_url: str | None = None):
        self.bucket = bucket
        self.endpoint_url = endpoint_url
        raise NotImplementedError("S3Storage: wire up aioboto3 when S3 target is configured")

    async def save(self, path: str, content: bytes) -> str: ...
    async def delete(self, path: str) -> None: ...
    async def exists(self, path: str) -> bool: ...