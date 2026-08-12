
# ===== app/api/v1/embeddings.py =====
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.dependencies.auth import require_permission
from app.services.embedding_service import EmbeddingService
from app.repositories.embedding_repository import EmbeddingRepository
from app.schemas.embedding import EmbeddingRecordOut, EmbeddingRunOut, GenerateEmbeddingsRequest

router = APIRouter(prefix="/embeddings", tags=["embeddings"])

@router.post("/{document_id}/generate", response_model=EmbeddingRunOut)
async def generate(document_id: str, payload: GenerateEmbeddingsRequest, db: AsyncSession = Depends(get_db), _=Depends(require_permission("documents.upload"))):
    return await EmbeddingService(db).generate_embeddings(document_id, payload.types, payload.provider)

@router.get("/{document_id}", response_model=list[EmbeddingRecordOut])
async def list_embeddings(document_id: str, db: AsyncSession = Depends(get_db), _=Depends(require_permission("documents.read"))):
    return await EmbeddingRepository(db).get_active(document_id)

@router.post("/{document_id}/reindex", response_model=EmbeddingRunOut)
async def reindex(document_id: str, provider: str, db: AsyncSession = Depends(get_db), _=Depends(require_permission("settings.manage"))):
    return await EmbeddingService(db).reindex(document_id, provider)

@router.get("/models/available")
async def available_models(_=Depends(require_permission("documents.read"))):
    return {"providers": ["ollama", "sentence_transformers", "openai"], "default": "ollama"}
