# ===== app/repositories/parsing_repository.py =====
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.parsing import ParsingResult

class ParsingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, result: ParsingResult) -> ParsingResult:
        self.db.add(result)
        await self.db.commit()
        await self.db.refresh(result)
        return result

    async def get_latest(self, document_id: str) -> ParsingResult | None:
        result = await self.db.execute(
            select(ParsingResult).where(ParsingResult.document_id == document_id)
            .order_by(ParsingResult.created_at.desc()).limit(1)
        )
        return result.scalar_one_or_none()