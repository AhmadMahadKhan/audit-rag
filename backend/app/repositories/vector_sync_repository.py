# ===== app/repositories/vector_sync_repository.py =====
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.vector_sync import VectorSyncStatus

class VectorSyncRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def record(self, status: VectorSyncStatus) -> VectorSyncStatus:
        self.db.add(status)
        await self.db.commit()
        return status

    async def get_failed(self, limit: int = 100) -> list[VectorSyncStatus]:
        result = await self.db.execute(select(VectorSyncStatus).where(VectorSyncStatus.synced == False).limit(limit))
        return result.scalars().all()

    async def mark_synced(self, status: VectorSyncStatus):
        status.synced = True
        status.error_message = None
        await self.db.commit()