from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.canonical import CanonicalDocumentRecord

class CanonicalRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, record: CanonicalDocumentRecord) -> CanonicalDocumentRecord:
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        return record

    async def get_latest(self, document_id: str) -> CanonicalDocumentRecord | None:
        result = await self.db.execute(
            select(CanonicalDocumentRecord).where(CanonicalDocumentRecord.document_id == document_id)
            .order_by(CanonicalDocumentRecord.created_at.desc()).limit(1)
        )
        return result.scalar_one_or_none()
