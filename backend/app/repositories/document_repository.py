# ===== app/repositories/document_repository.py =====
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document import Document

class DocumentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_hash(self, file_hash: str) -> Document | None:
        result = await self.db.execute(select(Document).where(Document.file_hash == file_hash))
        return result.scalar_one_or_none()

    async def get_by_id(self, document_id: str) -> Document | None:
        result = await self.db.execute(select(Document).where(Document.id == document_id))
        return result.scalar_one_or_none()

    async def create(self, document: Document) -> Document:
        self.db.add(document)
        await self.db.commit()
        await self.db.refresh(document)
        return document

    async def list_by_user(self, user_id: str, skip: int = 0, limit: int = 50) -> list[Document]:
        result = await self.db.execute(
            select(Document).where(Document.user_id == user_id)
            .order_by(Document.created_at.desc()).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def delete(self, document: Document):
        await self.db.delete(document)
        await self.db.commit()
