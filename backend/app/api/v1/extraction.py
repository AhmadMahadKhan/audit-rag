
# # ===== app/api/v1/extraction.py =====

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.dependencies.auth import require_permission
from app.services.extraction_service import ExtractionService
from app.repositories.knowledge_repository import KnowledgeRepository
from app.schemas.knowledge import EntityOut, FactOut, LineItemOut, ExtractionRunOut

router = APIRouter(prefix="/extraction", tags=["extraction"])



@router.get("/search/entities", response_model=list[EntityOut])
async def search_entities(entity_type: str | None = None, value: str | None = None, db: AsyncSession = Depends(get_db), _=Depends(require_permission("documents.read"))):
    return await KnowledgeRepository(db).search_entities(entity_type, value)

@router.get("/search/facts", response_model=list[FactOut])
async def search_facts(fact_type: str | None = None, db: AsyncSession = Depends(get_db), _=Depends(require_permission("documents.read"))):
    return await KnowledgeRepository(db).search_facts(fact_type)

@router.post("/{document_id}/extract", response_model=ExtractionRunOut)
async def extract(document_id: str, use_ai: bool = Query(False), db: AsyncSession = Depends(get_db), _=Depends(require_permission("documents.upload"))):
    return await ExtractionService(db).extract_all(document_id, use_ai)

@router.get("/{document_id}/entities", response_model=list[EntityOut])
async def get_entities(document_id: str, db: AsyncSession = Depends(get_db), _=Depends(require_permission("documents.read"))):
    return await KnowledgeRepository(db).get_entities(document_id)

@router.get("/{document_id}/facts", response_model=list[FactOut])
async def get_facts(document_id: str, db: AsyncSession = Depends(get_db), _=Depends(require_permission("documents.read"))):
    return await KnowledgeRepository(db).get_facts(document_id)

@router.get("/{document_id}/line-items", response_model=list[LineItemOut])
async def get_line_items(document_id: str, db: AsyncSession = Depends(get_db), _=Depends(require_permission("documents.read"))):
    return await KnowledgeRepository(db).get_line_items(document_id)