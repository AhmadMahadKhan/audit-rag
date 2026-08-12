
# ===== app/repositories/classification_repository.py =====
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.classification import Classification

class ClassificationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, classification: Classification) -> Classification:
        self.db.add(classification)
        await self.db.commit()
        await self.db.refresh(classification)
        return classification

    async def get_latest_for_document(self, document_id: str) -> Classification | None:
        result = await self.db.execute(
            select(Classification).where(Classification.document_id == document_id)
            .order_by(Classification.created_at.desc()).limit(1)
        )
        return result.scalar_one_or_none()

    async def get_history(self, document_id: str) -> list[Classification]:
        result = await self.db.execute(
            select(Classification).where(Classification.document_id == document_id)
            .order_by(Classification.created_at.desc())
        )
        return result.scalars().all()
