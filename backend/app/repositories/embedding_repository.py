
# ===== app/repositories/embedding_repository.py =====
import hashlib
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.embedding import EmbeddingRecord, EmbeddingRun

def hash_content(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()

class EmbeddingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_active(self, document_id: str, embedding_type: str | None = None) -> list[EmbeddingRecord]:
        query = select(EmbeddingRecord).where(EmbeddingRecord.document_id == document_id, EmbeddingRecord.is_active == True)
        if embedding_type:
            query = query.where(EmbeddingRecord.embedding_type == embedding_type)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_hash(self, content_hash: str, model_name: str) -> EmbeddingRecord | None:
        result = await self.db.execute(
            select(EmbeddingRecord).where(EmbeddingRecord.content_hash == content_hash,
                                            EmbeddingRecord.model_name == model_name, EmbeddingRecord.is_active == True)
        )
        return result.scalar_one_or_none()

    async def deactivate_all(self, document_id: str, embedding_type: str | None = None):
        query = update(EmbeddingRecord).where(EmbeddingRecord.document_id == document_id)
        if embedding_type:
            query = query.where(EmbeddingRecord.embedding_type == embedding_type)
        await self.db.execute(query.values(is_active=False))
        await self.db.commit()

    async def bulk_create(self, records: list[EmbeddingRecord]):
        for r in records:
            self.db.add(r)
        await self.db.commit()

    async def create_run(self, run: EmbeddingRun) -> EmbeddingRun:
        self.db.add(run)
        await self.db.commit()
        await self.db.refresh(run)
        return run