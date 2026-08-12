
# ===== app/api/v1/classification.py =====
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.dependencies.auth import require_permission
from app.services.classification_service import ClassificationService
from app.repositories.classification_repository import ClassificationRepository
from app.schemas.classification import ClassificationOut, ReclassifyRequest
from app.classification.document_types import DOCUMENT_TYPES
from app.core.exceptions import DocumentNotFound

router = APIRouter(prefix="/classification", tags=["classification"])

@router.post("/{document_id}/classify", response_model=ClassificationOut)
async def classify(document_id: str, db: AsyncSession = Depends(get_db), _=Depends(require_permission("documents.upload"))):
    return await ClassificationService(db).classify_document(document_id)

@router.post("/{document_id}/reclassify", response_model=ClassificationOut)
async def reclassify(document_id: str, payload: ReclassifyRequest, db: AsyncSession = Depends(get_db), _=Depends(require_permission("rules.manage"))):
    return await ClassificationService(db).reclassify(document_id, payload.document_type)

@router.get("/{document_id}", response_model=ClassificationOut)
async def get_classification(document_id: str, db: AsyncSession = Depends(get_db), _=Depends(require_permission("documents.read"))):
    result = await ClassificationRepository(db).get_latest_for_document(document_id)
    if not result:
        raise DocumentNotFound("No classification found for this document")
    return result

@router.get("/{document_id}/history", response_model=list[ClassificationOut])
async def classification_history(document_id: str, db: AsyncSession = Depends(get_db), _=Depends(require_permission("documents.read"))):
    return await ClassificationRepository(db).get_history(document_id)

@router.get("/types/supported")
async def supported_types(_=Depends(require_permission("documents.read"))):
    return {"types": list(DOCUMENT_TYPES.keys())}
