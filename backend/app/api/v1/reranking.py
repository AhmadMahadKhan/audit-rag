# ===== app/api/v1/reranking.py =====
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.dependencies.auth import require_permission
from app.services.reranking_service import RerankingService
from app.schemas.reranking import RerankRequest, RerankResponse

router = APIRouter(prefix="/rerank", tags=["reranking"])

@router.post("/search", response_model=RerankResponse)
async def rerank_search(payload: RerankRequest, db: AsyncSession = Depends(get_db), user=Depends(require_permission("chat.use"))):
    return await RerankingService(db).retrieve_and_rerank(
        payload.query, payload.top_n, payload.filters, user.id, payload.provider,
    )

@router.get("/models/available")
async def available_rerankers(_=Depends(require_permission("documents.read"))):
    return {"providers": ["sentence_transformers", "jina"], "default": "sentence_transformers"}
