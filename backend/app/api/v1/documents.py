# ===== app/api/v1/documents.py =====
from fastapi import APIRouter, Depends, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.dependencies.auth import get_current_user, require_permission
from app.services.upload_service import UploadService
from app.repositories.document_repository import DocumentRepository
from app.schemas.document import DocumentOut, UploadBatchResponse
from app.core.exceptions import DocumentNotFound, AuthorizationError

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/upload", response_model=UploadBatchResponse)
async def upload_documents(
    files: list[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permission("documents.upload")),
):
    payload = [(f.filename, await f.read()) for f in files]
    results = await UploadService(db).upload_batch(payload, user.id)
    success = sum(1 for r in results if r["status"] != "failed")
    return {"results": results, "success_count": success, "failure_count": len(results) - success}

@router.get("", response_model=list[DocumentOut])
async def list_documents(
    skip: int = Query(0), limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db), user=Depends(require_permission("documents.read")),
):
    return await DocumentRepository(db).list_by_user(user.id, skip, limit)

@router.get("/{document_id}", response_model=DocumentOut)
async def get_document(document_id: str, db: AsyncSession = Depends(get_db), user=Depends(require_permission("documents.read"))):
    doc = await DocumentRepository(db).get_by_id(document_id)
    if not doc:
        raise DocumentNotFound(f"Document {document_id} not found")
    if doc.user_id != user.id and "documents.delete" not in getattr(user, "_token_permissions", []):
        raise AuthorizationError("Not your document")
    return doc

@router.delete("/{document_id}")
async def delete_document(document_id: str, db: AsyncSession = Depends(get_db), user=Depends(require_permission("documents.delete"))):
    repo = DocumentRepository(db)
    doc = await repo.get_by_id(document_id)
    if not doc:
        raise DocumentNotFound(f"Document {document_id} not found")
    from app.storage.factory import get_storage_backend
    await get_storage_backend().delete(doc.storage_path)
    await repo.delete(doc)
    return {"success": True}

