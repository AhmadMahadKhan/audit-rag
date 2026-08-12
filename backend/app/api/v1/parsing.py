# ===== app/api/v1/parsing.py =====
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.dependencies.auth import require_permission
from app.services.parsing_service import ParsingService
from app.repositories.parsing_repository import ParsingRepository
from app.schemas.parsing import ParsingResultOut, ParsingDetailOut
from app.core.exceptions import DocumentNotFound

router = APIRouter(prefix="/parsing", tags=["parsing"])

@router.post("/{document_id}/parse", response_model=ParsingResultOut)
async def parse_document(document_id: str, db: AsyncSession = Depends(get_db), _=Depends(require_permission("documents.upload"))):
    return await ParsingService(db).parse_document(document_id)

@router.get("/{document_id}", response_model=ParsingDetailOut)
async def get_parsing_result(document_id: str, db: AsyncSession = Depends(get_db), _=Depends(require_permission("documents.read"))):
    result = await ParsingRepository(db).get_latest(document_id)
    if not result:
        raise DocumentNotFound("No parsing result found for this document")
    return result