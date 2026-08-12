
# ===== app/api/v1/viewer.py =====
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.dependencies.auth import require_permission
from app.services.viewer_service import ViewerService
from app.schemas.viewer import DocumentViewerBundle, BoundingBoxOut, CitationResolveOut, DocumentSearchHit

router = APIRouter(prefix="/viewer", tags=["viewer"])

@router.get("/{document_id}/bundle")
async def get_bundle(document_id: str, db: AsyncSession = Depends(get_db), user=Depends(require_permission("documents.read"))):
    return await ViewerService(db).get_bundle(document_id, user)

@router.get("/{document_id}/bounding-boxes", response_model=list[BoundingBoxOut])
async def bounding_boxes(document_id: str, page: int | None = Query(None), db: AsyncSession = Depends(get_db), user=Depends(require_permission("documents.read"))):
    return await ViewerService(db).get_bounding_boxes(document_id, user, page)

@router.get("/{document_id}/citation/{chunk_id}", response_model=CitationResolveOut)
async def resolve_citation(document_id: str, chunk_id: str, db: AsyncSession = Depends(get_db), user=Depends(require_permission("documents.read"))):
    return await ViewerService(db).resolve_citation(document_id, chunk_id, user)

@router.get("/{document_id}/search", response_model=list[DocumentSearchHit])
async def search_in_document(document_id: str, q: str, db: AsyncSession = Depends(get_db), user=Depends(require_permission("documents.read"))):
    return await ViewerService(db).search_within_document(document_id, q, user)

@router.get("/{document_id}/original")
async def get_original_file(document_id: str, db: AsyncSession = Depends(get_db), user=Depends(require_permission("documents.read"))):
    """Streams the original stored file for rendering (PDF.js, docx viewer, etc.)."""
    from fastapi.responses import FileResponse
    import os
    from app.storage.factory import get_storage_backend
    doc = await ViewerService(db)._authorize(document_id, user)
    storage = get_storage_backend()
    full_path = os.path.join(storage.base_path, doc.storage_path)
    return FileResponse(full_path, media_type=doc.mime_type, filename=doc.original_filename)
