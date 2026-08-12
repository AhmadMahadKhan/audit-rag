from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.dependencies.auth import require_permission
from app.services.canonical_service import CanonicalService
from app.repositories.canonical_repository import CanonicalRepository
from app.schemas.canonical import CanonicalOut, CanonicalDetailOut
from app.canonical.schema import CDM_SCHEMA_VERSION
from app.core.exceptions import DocumentNotFound

router = APIRouter(prefix="/canonical", tags=["canonical"])

@router.post("/{document_id}/build", response_model=CanonicalOut)
async def build(document_id: str, db: AsyncSession = Depends(get_db), _=Depends(require_permission("documents.upload"))):
    return await CanonicalService(db).build_canonical(document_id)

@router.get("/{document_id}", response_model=CanonicalDetailOut)
async def get_canonical(document_id: str, db: AsyncSession = Depends(get_db), _=Depends(require_permission("documents.read"))):
    result = await CanonicalRepository(db).get_latest(document_id)
    if not result:
        raise DocumentNotFound("No canonical document found")
    return result

@router.get("/{document_id}/export")
async def export_json(document_id: str, db: AsyncSession = Depends(get_db), _=Depends(require_permission("documents.read"))):
    result = await CanonicalRepository(db).get_latest(document_id)
    if not result:
        raise DocumentNotFound("No canonical document found")
    return result.canonical_json

@router.get("/schema/version")
async def schema_version():
    return {"schema_version": CDM_SCHEMA_VERSION}