
# ===== app/services/viewer_service.py =====
"""
Aggregation layer — pulls from every prior phase's repository so the frontend
viewer gets one call per view instead of 8. Deliberately does NOT introduce
new storage; it's a read-only composition service.
"""
from app.repositories.document_repository import DocumentRepository
from app.repositories.classification_repository import ClassificationRepository
from app.repositories.parsing_repository import ParsingRepository
from app.repositories.canonical_repository import CanonicalRepository
from app.repositories.metadata_repository import MetadataRepository
from app.repositories.knowledge_repository import KnowledgeRepository
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.embedding_repository import EmbeddingRepository
from app.canonical.schema import CanonicalDocument
from app.core.exceptions import DocumentNotFound, AuthorizationError
from app.core.logging_config import logger

class ViewerService:
    def __init__(self, db):
        self.db = db
        self.doc_repo = DocumentRepository(db)
        self.classification_repo = ClassificationRepository(db)
        self.parsing_repo = ParsingRepository(db)
        self.canonical_repo = CanonicalRepository(db)
        self.metadata_repo = MetadataRepository(db)
        self.knowledge_repo = KnowledgeRepository(db)
        self.chunk_repo = ChunkRepository(db)
        self.embedding_repo = EmbeddingRepository(db)

    async def _authorize(self, document_id: str, user):
        doc = await self.doc_repo.get_by_id(document_id)
        if not doc:
            raise DocumentNotFound(f"Document {document_id} not found")
        if doc.user_id != user.id and "documents.delete" not in getattr(user, "_token_permissions", []):
            raise AuthorizationError("Not authorized to view this document")
        return doc

    async def get_bundle(self, document_id: str, user) -> dict:
        doc = await self._authorize(document_id, user)

        classification = await self.classification_repo.get_latest_for_document(document_id)
        parsing = await self.parsing_repo.get_latest(document_id)
        canonical = await self.canonical_repo.get_latest(document_id)
        metadata = await self.metadata_repo.get_for_document(document_id)
        entities = await self.knowledge_repo.get_entities(document_id)
        facts = await self.knowledge_repo.get_facts(document_id)
        line_items = await self.knowledge_repo.get_line_items(document_id)
        chunks = await self.chunk_repo.get_for_document(document_id)
        embeddings = await self.embedding_repo.get_active(document_id)

        logger.info("document_viewer_opened", document_id=document_id, user_id=user.id)

        return {
            "document": {
                "id": doc.id, "filename": doc.original_filename, "mime_type": doc.mime_type,
                "file_size": doc.file_size, "document_type": doc.document_type,
                "processing_status": doc.processing_status, "created_at": doc.created_at.isoformat(),
            },
            "classification": {
                "document_type": classification.document_type, "confidence": classification.confidence,
                "status": classification.status,
            } if classification else None,
            "parsing": {
                "parser_name": parsing.parser_name, "ocr_used": parsing.ocr_used, "status": parsing.status,
                "processing_time_ms": parsing.processing_time_ms,
            } if parsing else None,
            "canonical_summary": {
                "page_count": canonical.canonical_json.get("info", {}).get("page_count"),
                "validation_status": canonical.validation_status, "validation_issues": canonical.validation_issues,
            } if canonical else None,
            "metadata": [{"key": m.key, "value": m.value, "category": m.category, "confidence": m.confidence,
                          "status": m.status} for m in metadata],
            "entities": [{"id": e.id, "type": e.entity_type, "value": e.value, "page": e.page,
                         "block_id": e.block_id, "bbox": e.bbox, "confidence": e.confidence} for e in entities],
            "facts": [{"id": f.id, "type": f.fact_type, "value": f.value, "confidence": f.confidence,
                      "status": f.status, "note": f.validation_note} for f in facts],
            "line_items": [{"id": li.id, "item": li.item_name, "qty": li.quantity, "unit_price": li.unit_price,
                            "total": li.line_total, "status": li.validation_status} for li in line_items],
            "chunks": [{"id": c.id, "index": c.chunk_index, "type": c.chunk_type, "section": c.section_name,
                       "pages": c.pages, "token_count": c.token_count, "status": c.validation_status} for c in chunks],
            "embedding_status": {
                "total": len(embeddings), "by_type": self._count_by_type(embeddings),
            },
        }

    def _count_by_type(self, embeddings) -> dict:
        counts = {}
        for e in embeddings:
            counts[e.embedding_type] = counts.get(e.embedding_type, 0) + 1
        return counts

    async def get_bounding_boxes(self, document_id: str, user, page: int | None = None) -> list[dict]:
        await self._authorize(document_id, user)
        canonical = await self.canonical_repo.get_latest(document_id)
        if not canonical:
            raise DocumentNotFound("No canonical document available")
        doc = CanonicalDocument(**canonical.canonical_json)

        boxes = []
        for block in doc.blocks:
            if block.bbox and (page is None or block.page == page):
                boxes.append({
                    "block_id": block.block_id, "page": block.page, "x": block.bbox.x, "y": block.bbox.y,
                    "width": block.bbox.width, "height": block.bbox.height, "type": block.type,
                    "text": block.text[:200], "confidence": block.confidence,
                })
        return boxes

    async def resolve_citation(self, document_id: str, chunk_id: str, user) -> dict:
        """Given a chat citation (document_id + chunk_id), returns everything
        the viewer needs to jump to and highlight that exact location."""
        await self._authorize(document_id, user)
        chunk = await self.chunk_repo.get_by_id(chunk_id)
        if not chunk or chunk.document_id != document_id:
            raise DocumentNotFound("Chunk not found for this document")

        canonical = await self.canonical_repo.get_latest(document_id)
        bbox = None
        if canonical and chunk.block_ids:
            doc = CanonicalDocument(**canonical.canonical_json)
            first_block = next((b for b in doc.blocks if b.block_id == chunk.block_ids[0]), None)
            if first_block and first_block.bbox:
                bbox = first_block.bbox.model_dump()

        return {
            "document_id": document_id, "chunk_id": chunk.id,
            "page": chunk.pages[0] if chunk.pages else None,
            "section_name": chunk.section_name, "bbox": bbox, "content": chunk.content,
        }

    async def search_within_document(self, document_id: str, query: str, user) -> list[dict]:
        await self._authorize(document_id, user)
        canonical = await self.canonical_repo.get_latest(document_id)
        if not canonical:
            return []
        doc = CanonicalDocument(**canonical.canonical_json)

        query_lower = query.lower()
        hits = []
        for block in doc.blocks:
            idx = block.text.lower().find(query_lower)
            if idx != -1:
                hits.append({
                    "block_id": block.block_id, "page": block.page, "text": block.text,
                    "match_start": idx, "match_end": idx + len(query),
                })
        return hits