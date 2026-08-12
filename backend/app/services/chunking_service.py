
# ===== app/services/chunking_service.py =====
from app.canonical.schema import CanonicalDocument
from app.chunking.registry import get_chunker
from app.chunking.validator import validate_chunk, deduplicate
from app.chunking.token_utils import estimate_tokens
from app.models.chunk import Chunk, ChunkingRun
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.canonical_repository import CanonicalRepository
from app.repositories.document_repository import DocumentRepository
from app.services.activity_logger import log_activity
from app.core.exceptions import DocumentNotFound, ValidationFailed
from app.core.logging_config import logger

class ChunkingService:
    def __init__(self, db):
        self.db = db
        self.repo = ChunkRepository(db)
        self.canonical_repo = CanonicalRepository(db)
        self.doc_repo = DocumentRepository(db)

    async def chunk_document(self, document_id: str) -> ChunkingRun:
        document = await self.doc_repo.get_by_id(document_id)
        if not document:
            raise DocumentNotFound(f"Document {document_id} not found")

        canonical_record = await self.canonical_repo.get_latest(document_id)
        if not canonical_record:
            raise ValidationFailed("No canonical document available")
        doc = CanonicalDocument(**canonical_record.canonical_json)

        chunker = get_chunker(document.document_type or "unknown")
        candidates = chunker.chunk(doc)
        candidates = deduplicate(candidates)

        chunk_rows = []
        invalid_count = 0
        prev_id = None
        for idx, cand in enumerate(candidates):
            status, issue = validate_chunk(cand)
            if status != "valid":
                invalid_count += 1
            chunk = Chunk(
                document_id=document_id, chunk_index=idx, chunk_type=cand.chunk_type, content=cand.content,
                section_name=cand.section_name, pages=cand.pages, block_ids=cand.block_ids,
                heading_path=cand.heading_path, token_count=estimate_tokens(cand.content),
                char_count=len(cand.content), chunker_name=chunker.name, validation_status=status,
            )
            chunk_rows.append(chunk)

        # link prev/next after creation (needs ids) — done via a second pass post-insert
        await self.repo.replace_all(document_id, chunk_rows)
        stored = await self.repo.get_for_document(document_id)
        for i, chunk in enumerate(stored):
            chunk.prev_chunk_id = stored[i - 1].id if i > 0 else None
            chunk.next_chunk_id = stored[i + 1].id if i < len(stored) - 1 else None
        await self.db.commit()

        run = await self.repo.create_run(ChunkingRun(
            document_id=document_id, chunker_used=chunker.name, chunk_count=len(chunk_rows),
            invalid_chunk_count=invalid_count, status="completed" if invalid_count == 0 else "needs_review",
        ))

        document.processing_status = "chunked"
        await self.db.commit()

        logger.info("chunking_completed", document_id=document_id, chunker=chunker.name, chunks=len(chunk_rows))
        await log_activity(self.db, "document_chunked", user_id=document.user_id, related_document_id=document_id)
        return run
