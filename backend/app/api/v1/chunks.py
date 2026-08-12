
# ===== app/api/v1/chunks.py =====
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.dependencies.auth import require_permission
from app.services.chunking_service import ChunkingService
from app.repositories.chunk_repository import ChunkRepository
from app.schemas.chunk import ChunkOut, ChunkingRunOut
from app.core.exceptions import DocumentNotFound

router = APIRouter(prefix="/chunks", tags=["chunks"])

@router.post("/{document_id}/generate", response_model=ChunkingRunOut)
async def generate_chunks(document_id: str, db: AsyncSession = Depends(get_db), _=Depends(require_permission("documents.upload"))):
    return await ChunkingService(db).chunk_document(document_id)

@router.get("/{document_id}", response_model=list[ChunkOut])
async def list_chunks(document_id: str, db: AsyncSession = Depends(get_db), _=Depends(require_permission("documents.read"))):
    return await ChunkRepository(db).get_for_document(document_id)

@router.get("/chunk/{chunk_id}", response_model=ChunkOut)
async def get_chunk(chunk_id: str, db: AsyncSession = Depends(get_db), _=Depends(require_permission("documents.read"))):
    chunk = await ChunkRepository(db).get_by_id(chunk_id)
    if not chunk:
        raise DocumentNotFound("Chunk not found")
    return chunk

@router.post("/{document_id}/rechunk", response_model=ChunkingRunOut)
async def rechunk(document_id: str, db: AsyncSession = Depends(get_db), _=Depends(require_permission("documents.upload"))):
    return await ChunkingService(db).chunk_document(document_id)
