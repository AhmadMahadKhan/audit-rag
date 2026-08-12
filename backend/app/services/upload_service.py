# ===== app/services/upload_service.py =====
import uuid
from app.models.document import Document, UploadStatus
from app.repositories.document_repository import DocumentRepository
from app.services.file_validator import FileValidator
from app.services.hash_service import compute_sha256
from app.storage.factory import get_storage_backend
from app.services.activity_logger import log_activity
from app.core.exceptions import DuplicateDocument, InvalidDocument
from app.core.config import settings
from app.core.logging_config import logger

class UploadService:
    def __init__(self, db):
        self.db = db
        self.repo = DocumentRepository(db)
        self.validator = FileValidator()
        self.storage = get_storage_backend()

    async def upload_one(self, filename: str, content: bytes, user_id: str) -> Document:
        try:
            safe_name = self.validator.sanitize_filename(filename)
            mime_type = self.validator.validate(filename, content)
            file_hash = compute_sha256(content)

            existing = await self.repo.get_by_hash(file_hash)
            if existing:
                if settings.DUPLICATE_POLICY == "reject":
                    raise DuplicateDocument(f"Duplicate of document {existing.id}")
                # replace/version/keep_both left as extension points

            ext = safe_name.rsplit(".", 1)[-1].lower()
            storage_filename = f"{uuid.uuid4()}.{ext}"
            storage_path = f"{user_id}/{storage_filename}"

            document = Document(
                user_id=user_id, original_filename=safe_name, storage_filename=storage_filename,
                storage_path=storage_path, storage_provider=settings.STORAGE_PROVIDER,
                file_size=len(content), mime_type=mime_type, file_extension=ext,
                file_hash=file_hash, status=UploadStatus.VALIDATING,
            )

            await self.storage.save(storage_path, content)
            document.status = UploadStatus.STORED
            document = await self.repo.create(document)

            await log_activity(self.db, "document_uploaded", user_id=user_id,
                                related_document_id=document.id, detail=safe_name)
            return document

        except (InvalidDocument, DuplicateDocument) as e:
            logger.warning("upload_rejected", filename=filename, reason=str(e))
            raise
        except Exception as e:
            logger.error("upload_failed", filename=filename, error=str(e))
            raise

    async def upload_batch(self, files: list[tuple[str, bytes]], user_id: str) -> list[dict]:
        results = []
        for filename, content in files:
            try:
                doc = await self.upload_one(filename, content, user_id)
                results.append({"filename": filename, "document_id": doc.id, "status": doc.status, "error": None})
            except Exception as e:
                results.append({"filename": filename, "document_id": None, "status": "failed", "error": str(e)})
        return results