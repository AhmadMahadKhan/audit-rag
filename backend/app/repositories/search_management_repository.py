# ===== app/repositories/search_management_repository.py =====
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.search_management import SavedSearch
from app.models.search import SearchLog

class SearchManagementRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_recent_history(self, user_id: str, limit: int = 20) -> list[SearchLog]:
        result = await self.db.execute(
            select(SearchLog).where(SearchLog.user_id == user_id)
            .order_by(SearchLog.created_at.desc()).limit(limit)
        )
        return result.scalars().all()

    async def delete_history_entry(self, log_id: str, user_id: str):
        await self.db.execute(delete(SearchLog).where(SearchLog.id == log_id, SearchLog.user_id == user_id))
        await self.db.commit()

    async def clear_history(self, user_id: str):
        await self.db.execute(delete(SearchLog).where(SearchLog.user_id == user_id))
        await self.db.commit()

    async def create_saved_search(self, saved: SavedSearch) -> SavedSearch:
        self.db.add(saved)
        await self.db.commit()
        await self.db.refresh(saved)
        return saved

    async def list_saved_searches(self, user_id: str) -> list[SavedSearch]:
        result = await self.db.execute(
            select(SavedSearch).where(SavedSearch.user_id == user_id)
            .order_by(SavedSearch.is_favorite.desc(), SavedSearch.created_at.desc())
        )
        return result.scalars().all()

    async def get_saved_search(self, search_id: str, user_id: str) -> SavedSearch | None:
        result = await self.db.execute(
            select(SavedSearch).where(SavedSearch.id == search_id, SavedSearch.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def delete_saved_search(self, saved: SavedSearch):
        await self.db.delete(saved)
        await self.db.commit()

    async def get_popular_queries(self, limit: int = 10) -> list[tuple[str, int]]:
        from sqlalchemy import func
        result = await self.db.execute(
            select(SearchLog.query, func.count(SearchLog.id).label("cnt"))
            .group_by(SearchLog.query).order_by(func.count(SearchLog.id).desc()).limit(limit)
        )
        return result.all()
