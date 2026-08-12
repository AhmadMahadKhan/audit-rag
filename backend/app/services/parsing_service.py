# ===== app/services/parsing_service.py =====
import os
from app.parsing.registry import get_parser
from app.repositories.parsing_repository import ParsingRepository
from app.repositories.document_repository import DocumentRepository
from app.models.parsing import ParsingResult
from app.services.activity_logger import log_activity
from app.storage.factory import get_storage_backend
from app.core.exceptions import DocumentNotFound, OCRFailed
from app.core.logging_config import logger

class ParsingService:
    def __init__(self, db):
        self.db = db
        self.repo = ParsingRepository(db)
        self.doc_repo = DocumentRepository(db)

    async def parse_document(self, document_id: str) -> ParsingResult:
        document = await self.doc_repo.get_by_id(document_id)
        if not document:
            raise DocumentNotFound(f"Document {document_id} not found")

        storage = get_storage_backend()
        full_path = os.path.join(storage.base_path, document.storage_path)
        with open(full_path, "rb") as f:
            content = f.read()

        try:
            parser = get_parser(document.file_extension)
            parsed = await parser.parse(document.id, content)
            status = "needs_review" if parsed.warnings else "completed"

            result = ParsingResult(
                document_id=document.id, parser_name=parsed.parser_name, parser_version=parsed.parser_version,
                ocr_used=parsed.ocr_used, status=status, processing_time_ms=parsed.processing_time_ms,
                raw_text=parsed.raw_text, parsed_json=parsed.model_dump(),
            )
            result = await self.repo.create(result)

            document.processing_status = "parsed"
            await self.db.commit()

            logger.info("parsing_completed", document_id=document_id, parser=parsed.parser_name, ocr=parsed.ocr_used)
            await log_activity(self.db, "document_parsed", user_id=document.user_id,
                                related_document_id=document_id, status=status)
            return result

        except Exception as e:
            logger.error("parsing_failed", document_id=document_id, error=str(e))
            result = ParsingResult(document_id=document.id, parser_name="unknown", parser_version="0",
                                     status="failed", error_message=str(e), parsed_json={})
            result = await self.repo.create(result)
            await log_activity(self.db, "document_parsed", user_id=document.user_id,
                                related_document_id=document_id, status="failed", detail=str(e))
            raise OCRFailed(str(e))
