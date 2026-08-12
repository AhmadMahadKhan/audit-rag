# ===== app/services/embedding_service.py =====
import asyncio
from app.embeddings.factory import get_embedding_provider
from app.embeddings.validator import validate_vector
from app.embeddings.content_builders import build_metadata_text, build_entity_text, build_summary_text
from app.models.embedding import EmbeddingRecord, EmbeddingRun
from app.repositories.embedding_repository import EmbeddingRepository, hash_content
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.metadata_repository import MetadataRepository
from app.repositories.knowledge_repository import KnowledgeRepository
from app.repositories.parsing_repository import ParsingRepository
from app.repositories.document_repository import DocumentRepository
from app.services.activity_logger import log_activity
from app.core.config import settings
from app.core.exceptions import DocumentNotFound, ValidationFailed
from app.core.logging_config import logger

class EmbeddingService:
    def __init__(self, db):
        self.db = db
        self.repo = EmbeddingRepository(db)
        self.chunk_repo = ChunkRepository(db)
        self.metadata_repo = MetadataRepository(db)
        self.knowledge_repo = KnowledgeRepository(db)
        self.parsing_repo = ParsingRepository(db)
        self.doc_repo = DocumentRepository(db)

    async def generate_embeddings(self, document_id: str, types: list[str] | None = None,
                                    provider_name: str | None = None) -> EmbeddingRun:
        document = await self.doc_repo.get_by_id(document_id)
        if not document:
            raise DocumentNotFound(f"Document {document_id} not found")

        types = types or ["text", "metadata", "entity", "table", "summary"]
        provider = get_embedding_provider(provider_name)

        all_records = []
        failed = 0

        if "text" in types:
            recs, fail = await self._embed_chunks(document_id, provider)
            all_records += recs; failed += fail

        if "table" in types:
            recs, fail = await self._embed_tables(document_id, provider)
            all_records += recs; failed += fail

        if "metadata" in types:
            recs, fail = await self._embed_metadata(document_id, provider)
            all_records += recs; failed += fail

        if "entity" in types:
            recs, fail = await self._embed_entities(document_id, provider)
            all_records += recs; failed += fail

        if "summary" in types:
            recs, fail = await self._embed_summary(document_id, provider)
            all_records += recs; failed += fail

        # deactivate old versions for the types being regenerated, then insert new
        for t in types:
            await self.repo.deactivate_all(document_id, t)
        await self.repo.bulk_create(all_records)

        run = await self.repo.create_run(EmbeddingRun(
            document_id=document_id, model_name=provider.name, embedding_types=types,
            total_count=len(all_records), failed_count=failed,
            status="completed" if failed == 0 else "needs_review",
        ))

        document.processing_status = "embedded"
        await self.db.commit()
        logger.info("embedding_completed", document_id=document_id, count=len(all_records), failed=failed)
        await log_activity(self.db, "embeddings_generated", user_id=document.user_id, related_document_id=document_id)
        return run

    async def _run_batch(self, texts: list[str], provider) -> list[list[float]]:
        vectors = []
        batch_size = settings.EMBEDDING_BATCH_SIZE
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            vectors.extend(await provider.embed(batch))
        return vectors

    async def _embed_chunks(self, document_id, provider):
        chunks = await self.chunk_repo.get_for_document(document_id)
        chunks = [c for c in chunks if c.validation_status == "valid"]
        if not chunks:
            return [], 0
        texts = [c.content for c in chunks]
        vectors = await self._run_batch(texts, provider)
        return self._build_records(document_id, "text", list(zip([c.id for c in chunks], texts, vectors)), provider)

    async def _embed_tables(self, document_id, provider):
        chunks = await self.chunk_repo.get_for_document(document_id)
        table_chunks = [c for c in chunks if c.chunk_type == "table"]
        if not table_chunks:
            return [], 0
        texts = [c.content for c in table_chunks]
        vectors = await self._run_batch(texts, provider)
        return self._build_records(document_id, "table", list(zip([c.id for c in table_chunks], texts, vectors)), provider)

    async def _embed_metadata(self, document_id, provider):
        fields = await self.metadata_repo.get_for_document(document_id)
        if not fields:
            return [], 0
        text = build_metadata_text([{"key": f.key, "value": f.value} for f in fields])
        if not text.strip():
            return [], 0
        vectors = await self._run_batch([text], provider)
        return self._build_records(document_id, "metadata", [(None, text, vectors[0])], provider)

    async def _embed_entities(self, document_id, provider):
        entities = await self.knowledge_repo.get_entities(document_id)
        if not entities:
            return [], 0
        texts = [build_entity_text(e.entity_type, e.value) for e in entities]
        vectors = await self._run_batch(texts, provider)
        return self._build_records(document_id, "entity",
                                     [(e.id, t, v) for e, t, v in zip(entities, texts, vectors)], provider, ref_is_source=True)

    async def _embed_summary(self, document_id, provider):
        parsing_result = await self.parsing_repo.get_latest(document_id)
        if not parsing_result or not parsing_result.raw_text:
            return [], 0
        text = build_summary_text(parsing_result.raw_text)
        vectors = await self._run_batch([text], provider)
        return self._build_records(document_id, "summary", [(None, text, vectors[0])], provider)

    def _build_records(self, document_id, embedding_type, triples, provider, ref_is_source=False):
        records, failed = [], 0
        for ref_id, text, vector in triples:
            status, issue = validate_vector(vector, provider.dimension)
            if status == "invalid":
                failed += 1
            record = EmbeddingRecord(
                document_id=document_id,
                chunk_id=None if (ref_is_source or embedding_type in ("metadata", "summary")) else ref_id,
                source_ref_id=ref_id if ref_is_source else None,
                embedding_type=embedding_type, model_name=provider.name, model_version=provider.model_version,
                vector_dimension=len(vector) if vector else provider.dimension, vector=vector,
                content_hash=hash_content(text), is_active=True, status=status, error_message=issue,
            )
            records.append(record)
        return records, failed

    async def reindex(self, document_id: str, new_provider_name: str) -> EmbeddingRun:
        """Full re-index with a different model — old vectors kept (is_active=False) for rollback."""
        return await self.generate_embeddings(document_id, types=None, provider_name=new_provider_name)
