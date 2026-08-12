# ===== app/api/v1/metadata.py =====
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.dependencies.auth import require_permission
from app.services.metadata_service import MetadataService
from app.repositories.metadata_repository import MetadataRepository
from app.schemas.metadata import MetadataFieldOut, MetadataUpdateRequest, MetadataSearchRequest, ExtractionRunOut

router = APIRouter(prefix="/metadata", tags=["metadata"])

@router.post("/{document_id}/extract", response_model=ExtractionRunOut)
async def extract(document_id: str, db: AsyncSession = Depends(get_db), _=Depends(require_permission("documents.upload"))):
    return await MetadataService(db).extract_metadata(document_id)

@router.get("/{document_id}", response_model=list[MetadataFieldOut])
async def get_metadata(document_id: str, db: AsyncSession = Depends(get_db), _=Depends(require_permission("documents.read"))):
    return await MetadataRepository(db).get_for_document(document_id)

@router.put("/{document_id}")
async def update_metadata(document_id: str, payload: MetadataUpdateRequest, db: AsyncSession = Depends(get_db), _=Depends(require_permission("documents.upload"))):
    await MetadataService(db).update_field(document_id, payload.key, payload.value)
    return {"success": True}

@router.post("/search")
async def search(payload: MetadataSearchRequest, db: AsyncSession = Depends(get_db), _=Depends(require_permission("documents.read"))):
    document_ids = await MetadataRepository(db).search(payload.filters, payload.skip, payload.limit)
    return {"document_ids": document_ids}

@router.get("/{document_id}/export")
async def export(document_id: str, db: AsyncSession = Depends(get_db), _=Depends(require_permission("documents.read"))):
    fields = await MetadataRepository(db).get_for_document(document_id)
    return {f.key: f.value for f in fields}