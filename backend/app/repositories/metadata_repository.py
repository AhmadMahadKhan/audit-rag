# ===== app/repositories/metadata_repository.py =====
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.metadata import DocumentMetadata, MetadataExtractionRun

class MetadataRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def replace_all(self, document_id: str, fields: list[DocumentMetadata]):
        await self.db.execute(delete(DocumentMetadata).where(DocumentMetadata.document_id == document_id))
        for f in fields:
            self.db.add(f)
        await self.db.commit()

    async def get_for_document(self, document_id: str) -> list[DocumentMetadata]:
        result = await self.db.execute(select(DocumentMetadata).where(DocumentMetadata.document_id == document_id))
        return result.scalars().all()

    async def search(self, filters: dict, skip: int = 0, limit: int = 50) -> list[str]:
        """filters: {key: value} — returns matching document_ids (AND across keys)."""
        query = select(DocumentMetadata.document_id).distinct()
        for key, value in filters.items():
            sub = select(DocumentMetadata.document_id).where(
                DocumentMetadata.key == key, DocumentMetadata.value.ilike(f"%{value}%")
            )
            query = query.where(DocumentMetadata.document_id.in_(sub))
        result = await self.db.execute(query.offset(skip).limit(limit))
        return [r[0] for r in result.all()]

    async def create_run(self, run: MetadataExtractionRun) -> MetadataExtractionRun:
        self.db.add(run)
        await self.db.commit()
        await self.db.refresh(run)
        return run