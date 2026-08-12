# ===== app/api/v1/search_ui.py =====
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.dependencies.auth import require_permission
from app.services.search_ui_service import SearchUIService
from app.repositories.search_management_repository import SearchManagementRepository
from app.schemas.search_ui import (
    SearchUIRequest, SearchResultOut, SearchHistoryOut, SavedSearchOut, SaveSearchRequest,
)

router = APIRouter(prefix="/search", tags=["search-ui"])

@router.post("", response_model=list[SearchResultOut])
async def search(payload: SearchUIRequest, db: AsyncSession = Depends(get_db), user=Depends(require_permission("documents.read"))):
    return await SearchUIService(db).search(payload.query, payload.mode, payload.filters, user.id, payload.top_k)

@router.get("/suggestions")
async def suggestions(q: str = Query(..., min_length=1), db: AsyncSession = Depends(get_db), user=Depends(require_permission("documents.read"))):
    return {"suggestions": await SearchUIService(db).suggest(q, user.id)}

@router.get("/history", response_model=list[SearchHistoryOut])
async def get_history(db: AsyncSession = Depends(get_db), user=Depends(require_permission("documents.read"))):
    return await SearchManagementRepository(db).get_recent_history(user.id)

@router.delete("/history/{log_id}")
async def delete_history_entry(log_id: str, db: AsyncSession = Depends(get_db), user=Depends(require_permission("documents.read"))):
    await SearchManagementRepository(db).delete_history_entry(log_id, user.id)
    return {"success": True}

@router.delete("/history")
async def clear_history(db: AsyncSession = Depends(get_db), user=Depends(require_permission("documents.read"))):
    await SearchManagementRepository(db).clear_history(user.id)
    return {"success": True}

@router.post("/saved", response_model=SavedSearchOut)
async def save_search(payload: SaveSearchRequest, db: AsyncSession = Depends(get_db), user=Depends(require_permission("documents.read"))):
    return await SearchUIService(db).save_search(user.id, payload.name, payload.query, payload.filters, payload.search_mode)

@router.get("/saved", response_model=list[SavedSearchOut])
async def list_saved(db: AsyncSession = Depends(get_db), user=Depends(require_permission("documents.read"))):
    return await SearchManagementRepository(db).list_saved_searches(user.id)

@router.post("/saved/{search_id}/run", response_model=list[SearchResultOut])
async def run_saved(search_id: str, db: AsyncSession = Depends(get_db), user=Depends(require_permission("documents.read"))):
    return await SearchUIService(db).run_saved_search(search_id, user.id)

@router.delete("/saved/{search_id}")
async def delete_saved(search_id: str, db: AsyncSession = Depends(get_db), user=Depends(require_permission("documents.read"))):
    repo = SearchManagementRepository(db)
    saved = await repo.get_saved_search(search_id, user.id)
    if saved:
        await repo.delete_saved_search(saved)
    return {"success": True}