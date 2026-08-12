# ===== app/api/v1/retrieval.py =====
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.dependencies.auth import require_permission, get_current_user
from app.services.retrieval_service import RetrievalService
from app.schemas.retrieval import SearchRequestIn, ContextItem

router = APIRouter(prefix="/retrieval", tags=["retrieval"])

@router.post("/hybrid", response_model=list[ContextItem])
async def hybrid_search(payload: SearchRequestIn, db: AsyncSession = Depends(get_db), user=Depends(require_permission("chat.use"))):
    return await RetrievalService(db).hybrid_search(payload.query, payload.top_k, payload.filters, user.id, payload.use_rewrite)

@router.post("/semantic")
async def semantic_search(payload: SearchRequestIn, db: AsyncSession = Depends(get_db), _=Depends(require_permission("chat.use"))):
    return await RetrievalService(db).semantic_search(payload.query, payload.top_k, payload.filters)

@router.get("/keyword/{document_id}")
async def keyword_search(document_id: str, q: str, top_k: int = 10, db: AsyncSession = Depends(get_db), _=Depends(require_permission("documents.read"))):
    return await RetrievalService(db).keyword_search(q, document_id, top_k)