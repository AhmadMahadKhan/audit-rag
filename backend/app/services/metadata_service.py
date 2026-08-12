# ===== app/services/metadata_service.py =====
from app.canonical.schema import CanonicalDocument
from app.metadata.registry import get_extractors
from app.metadata.normalizer import normalize_field
from app.metadata.validator import validate_field
from app.models.metadata import DocumentMetadata, MetadataExtractionRun
from app.repositories.metadata_repository import MetadataRepository
from app.repositories.canonical_repository import CanonicalRepository
from app.repositories.document_repository import DocumentRepository
from app.services.activity_logger import log_activity
from app.core.exceptions import DocumentNotFound, ValidationFailed
from app.core.logging_config import logger

class MetadataService:
    def __init__(self, db):
        self.db = db
        self.repo = MetadataRepository(db)
        self.canonical_repo = CanonicalRepository(db)
        self.doc_repo = DocumentRepository(db)

    async def extract_metadata(self, document_id: str) -> MetadataExtractionRun:
        document = await self.doc_repo.get_by_id(document_id)
        if not document:
            raise DocumentNotFound(f"Document {document_id} not found")

        canonical_record = await self.canonical_repo.get_latest(document_id)
        if not canonical_record:
            raise ValidationFailed("No canonical document available — run canonical build first")

        canonical_doc = CanonicalDocument(**canonical_record.canonical_json)

        raw_fields = []
        for extractor in get_extractors():
            try:
                raw_fields.extend(extractor.extract(canonical_doc))
            except Exception as e:
                logger.error("metadata_extractor_failed", extractor=extractor.name, error=str(e))

        db_rows = []
        low_confidence_count = 0
        for field in raw_fields:
            field = normalize_field(field)
            status, issue = validate_field(field)
            if status == "needs_review":
                low_confidence_count += 1
            db_rows.append(DocumentMetadata(
                document_id=document_id, key=field.key, value=field.value, category=field.category,
                confidence=field.confidence, extractor=field.extractor, extractor_version="1.0", status=status,
            ))

        await self.repo.replace_all(document_id, db_rows)

        overall_confidence = (sum(f.confidence for f in raw_fields) / len(raw_fields)) if raw_fields else 0.0
        run = await self.repo.create_run(MetadataExtractionRun(
            document_id=document_id, overall_confidence=overall_confidence,
            status="completed" if low_confidence_count == 0 else "needs_review",
            field_count=len(db_rows), low_confidence_count=low_confidence_count,
        ))

        document.processing_status = "metadata_extracted"
        await self.db.commit()

        logger.info("metadata_extraction_completed", document_id=document_id, fields=len(db_rows), low_confidence=low_confidence_count)
        await log_activity(self.db, "metadata_extracted", user_id=document.user_id, related_document_id=document_id)
        return run

    async def update_field(self, document_id: str, key: str, value: str):
        from sqlalchemy import select
        result = await self.db.execute(
            select(DocumentMetadata).where(DocumentMetadata.document_id == document_id, DocumentMetadata.key == key)
        )
        field = result.scalar_one_or_none()
        if field:
            field.value = value
            field.status = "valid"
            field.extractor = "manual"
        else:
            self.db.add(DocumentMetadata(document_id=document_id, key=key, value=value, category="business",
                                           confidence=1.0, extractor="manual", extractor_version="1.0", status="valid"))
        await self.db.commit()