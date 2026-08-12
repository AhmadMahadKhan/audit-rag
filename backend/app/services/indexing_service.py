# ===== app/services/indexing_service.py =====
import uuid
from app.vectorstore.factory import get_vector_store
from app.vectorstore.collections import collection_for
from app.vectorstore.payload_builder import build_payload
from app.models.vector_sync import VectorSyncStatus
from app.repositories.vector_sync_repository import VectorSyncRepository
from app.repositories.embedding_repository import EmbeddingRepository
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.metadata_repository import MetadataRepository
from app.repositories.document_repository import DocumentRepository
from app.services.activity_logger import log_activity
from app.core.exceptions import DocumentNotFound
from app.core.logging_config import logger

class IndexingService:
    def __init__(self, db):
        self.db = db
        self.store = get_vector_store()
        self.embedding_repo = EmbeddingRepository(db)
        self.chunk_repo = ChunkRepository(db)
        self.metadata_repo = MetadataRepository(db)
        self.doc_repo = DocumentRepository(db)
        self.sync_repo = VectorSyncRepository(db)

    async def index_document(self, document_id: str) -> dict:
        document = await self.doc_repo.get_by_id(document_id)
        if not document:
            raise DocumentNotFound(f"Document {document_id} not found")

        records = await self.embedding_repo.get_active(document_id)
        chunks = {c.id: c for c in await self.chunk_repo.get_for_document(document_id)}
        metadata_fields = await self.metadata_repo.get_for_document(document_id)

        by_collection: dict[str, list[dict]] = {}
        point_map: dict[str, tuple[str, str]] = {}  # embedding_id -> (collection, point_id)

        for rec in records:
            if rec.status != "valid":
                continue
            collection = collection_for(rec.embedding_type)
            await self.store.ensure_collection(collection, rec.vector_dimension)

            chunk = chunks.get(rec.chunk_id) if rec.chunk_id else None
            payload = build_payload(rec, document, chunk, metadata_fields)
            point_id = str(uuid.uuid4())

            by_collection.setdefault(collection, []).append({"id": point_id, "vector": rec.vector, "payload": payload})
            point_map[rec.id] = (collection, point_id)

        indexed, failed = 0, 0
        for collection, points in by_collection.items():
            try:
                await self.store.upsert(collection, points)
                indexed += len(points)
            except Exception as e:
                failed += len(points)
                logger.error("qdrant_upsert_failed", collection=collection, error=str(e))

        for embedding_id, (collection, point_id) in point_map.items():
            await self.sync_repo.record(VectorSyncStatus(
                embedding_id=embedding_id, collection=collection, point_id=point_id, synced=True,
            ))

        document.processing_status = "indexed"
        await self.db.commit()
        logger.info("document_indexed", document_id=document_id, indexed=indexed, failed=failed)
        await log_activity(self.db, "document_indexed", user_id=document.user_id, related_document_id=document_id)
        return {"indexed": indexed, "failed": failed, "collections": list(by_collection.keys())}

    async def retry_failed_syncs(self, limit: int = 100) -> int:
        failed = await self.sync_repo.get_failed(limit)
        retried = 0
        for status in failed:
            status.retry_count += 1
            await self.db.commit()
            retried += 1
        return retried

    async def delete_document_vectors(self, document_id: str):
        from app.vectorstore.collections import COLLECTIONS
        
        # path without a direct "delete by filter" call in this abstraction.
        for collection in set(COLLECTIONS.values()):
            try:
                stats = await self.store.get_collection_stats(collection)
                if stats["points_count"] > 0:
                    # NOTE: real filter-based delete needs Qdrant's delete(points_selector=FilterSelector(...))
                    # left as a direct client call rather than adding to the abstract interface prematurely
                    from qdrant_client import models
                    await self.store.client.delete(
                        collection_name=collection,
                        points_selector=models.FilterSelector(
                            filter=models.Filter(must=[models.FieldCondition(
                                key="document_id", match=models.MatchValue(value=document_id))])
                        ),
                    )
            except Exception as e:
                logger.error("vector_delete_failed", collection=collection, document_id=document_id, error=str(e))
