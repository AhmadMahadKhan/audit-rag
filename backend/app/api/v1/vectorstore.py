# ===== app/api/v1/vectorstore.py =====
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.dependencies.auth import require_permission
from app.services.indexing_service import IndexingService
from app.services.search_service import SearchService
from app.schemas.vectorstore import IndexResult, SearchRequest, SearchResultItem, CollectionStats

router = APIRouter(prefix="/vectorstore", tags=["vectorstore"])

@router.post("/{document_id}/index", response_model=IndexResult)
async def index_document(document_id: str, db: AsyncSession = Depends(get_db), _=Depends(require_permission("documents.upload"))):
    return await IndexingService(db).index_document(document_id)

@router.delete("/{document_id}/index")
async def delete_index(document_id: str, db: AsyncSession = Depends(get_db), _=Depends(require_permission("documents.delete"))):
    await IndexingService(db).delete_document_vectors(document_id)
    return {"success": True}

@router.post("/search", response_model=list[SearchResultItem])
async def search(payload: SearchRequest, db: AsyncSession = Depends(get_db), _=Depends(require_permission("chat.use"))):
    return await SearchService(db).search(payload.query, payload.embedding_type, payload.top_k, payload.filters)

@router.get("/stats")
async def stats(db: AsyncSession = Depends(get_db), _=Depends(require_permission("analytics.read"))):
    return await SearchService(db).collection_stats()

@router.post("/sync/retry")
async def retry_sync(db: AsyncSession = Depends(get_db), _=Depends(require_permission("settings.manage"))):
    count = await IndexingService(db).retry_failed_syncs()
    return {"retried": count}