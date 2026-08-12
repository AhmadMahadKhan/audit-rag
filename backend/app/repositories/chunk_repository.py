
# ===== app/repositories/chunk_repository.py =====
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.chunk import Chunk, ChunkingRun

class ChunkRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def replace_all(self, document_id: str, chunks: list[Chunk]):
        await self.db.execute(delete(Chunk).where(Chunk.document_id == document_id))
        for c in chunks:
            self.db.add(c)
        await self.db.commit()

    async def get_for_document(self, document_id: str) -> list[Chunk]:
        result = await self.db.execute(
            select(Chunk).where(Chunk.document_id == document_id).order_by(Chunk.chunk_index)
        )
        return result.scalars().all()

    async def get_by_id(self, chunk_id: str) -> Chunk | None:
        result = await self.db.execute(select(Chunk).where(Chunk.id == chunk_id))
        return result.scalar_one_or_none()

    async def create_run(self, run: ChunkingRun) -> ChunkingRun:
        self.db.add(run)
        await self.db.commit()
        await self.db.refresh(run)
        return run