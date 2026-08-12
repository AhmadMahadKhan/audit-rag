from app.parsing.schema import ParsedDocument
from app.canonical.transformer import transform_to_canonical
from app.canonical.validator import validate_canonical_document
from app.canonical.schema import CDM_SCHEMA_VERSION
from app.repositories.canonical_repository import CanonicalRepository
from app.repositories.parsing_repository import ParsingRepository
from app.repositories.document_repository import DocumentRepository
from app.models.canonical import CanonicalDocumentRecord
from app.core.exceptions import DocumentNotFound, ValidationFailed
from app.core.logging_config import logger

class CanonicalService:
    def __init__(self, db):
        self.db = db
        self.repo = CanonicalRepository(db)
        self.parsing_repo = ParsingRepository(db)
        self.doc_repo = DocumentRepository(db)

    async def build_canonical(self, document_id: str) -> CanonicalDocumentRecord:
        document = await self.doc_repo.get_by_id(document_id)
        if not document:
            raise DocumentNotFound(f"Document {document_id} not found")

        parsing_result = await self.parsing_repo.get_latest(document_id)
        if not parsing_result or parsing_result.status == "failed":
            raise ValidationFailed("No successful parsing result to build canonical document from")

        parsed = ParsedDocument(**parsing_result.parsed_json)
        canonical = transform_to_canonical(parsed, {
            "file_name": document.original_filename, "file_type": document.file_extension,
            "mime_type": document.mime_type, "file_size": document.file_size, "file_hash": document.file_hash,
        })

        issues = validate_canonical_document(canonical)
        canonical.processing.validation_status = "invalid" if issues else "valid"

        record = CanonicalDocumentRecord(
            document_id=document_id, schema_version=CDM_SCHEMA_VERSION,
            validation_status=canonical.processing.validation_status,
            validation_issues=issues, canonical_json=canonical.model_dump(mode="json"),
        )
        record = await self.repo.create(record)

        document.processing_status = "canonicalized" if not issues else "canonicalized_with_issues"
        await self.db.commit()

        logger.info("canonical_document_built", document_id=document_id, valid=not issues, issue_count=len(issues))
        return record