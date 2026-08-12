from app.classification.factory import get_classifier
from app.classification.document_types import get_pipeline
from app.models.classification import Classification
from app.repositories.classification_repository import ClassificationRepository
from app.repositories.document_repository import DocumentRepository
from app.services.activity_logger import log_activity
from app.core.config import settings
from app.core.exceptions import DocumentNotFound
from app.core.logging_config import logger
from app.storage.factory import get_storage_backend
import os

class ClassificationService:
    def __init__(self, db):
        self.db = db
        self.repo = ClassificationRepository(db)
        self.doc_repo = DocumentRepository(db)

    async def classify_document(self, document_id: str, method_override: str | None = None) -> Classification:
        document = await self.doc_repo.get_by_id(document_id)
        if not document:
            raise DocumentNotFound(f"Document {document_id} not found")

        storage = get_storage_backend()
        full_path = os.path.join(storage.base_path, document.storage_path)
        with open(full_path, "rb") as f:
            content = f.read()

        classifier = get_classifier()
        result = await classifier.classify(document.original_filename, document.mime_type, content)

        status = "completed" if result.confidence >= settings.CLASSIFICATION_CONFIDENCE_THRESHOLD else "needs_review"
        pipeline = get_pipeline(result.document_type)

        classification = Classification(
            document_id=document.id, document_type=result.document_type, confidence=result.confidence,
            method=result.method, model_version=result.model_version, pipeline=pipeline, status=status,
        )
        classification = await self.repo.create(classification)

        document.document_type = result.document_type
        await self.db.commit()

        logger.info("classification_completed", document_id=document_id, type=result.document_type,
                     confidence=result.confidence, status=status)
        await log_activity(self.db, "document_classified", user_id=document.user_id,
                            related_document_id=document_id, status=status, detail=result.document_type)

        return classification

    async def reclassify(self, document_id: str, manual_type: str | None = None) -> Classification:
        if manual_type:
            from app.classification.document_types import get_pipeline, DOCUMENT_TYPES
            if manual_type not in DOCUMENT_TYPES:
                from app.core.exceptions import ValidationFailed
                raise ValidationFailed(f"Unknown document type: {manual_type}")
            document = await self.doc_repo.get_by_id(document_id)
            classification = Classification(
                document_id=document_id, document_type=manual_type, confidence=1.0,
                method="manual", pipeline=get_pipeline(manual_type), status="completed",
            )
            classification = await self.repo.create(classification)
            document.document_type = manual_type
            await self.db.commit()
            return classification
        return await self.classify_document(document_id)