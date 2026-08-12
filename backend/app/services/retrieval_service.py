# ===== app/services/retrieval_service.py =====
"""
Full hybrid pipeline: query processing -> rewrite -> expand -> filter extraction
-> dense (Qdrant) + sparse (BM25) retrieval -> RRF fusion -> context assembly.

Caveat: BM25 index is rebuilt per-search-call from chunks currently returned
by a broad Qdrant scan/filter — not scanning the full corpus every query. For
very large corpora this should move to a persistent BM25 index (e.g. Postgres
full-text / Elasticsearch) rather than in-memory rebuild; flagged, not solved
here since it's an infra choice.
"""
import time
from app.retrieval.query_processing import normalize_query, correct_spelling, resolve_acronyms
from app.retrieval.query_rewriter import rewrite_query
from app.retrieval.query_expansion import expand_query
from app.retrieval.filter_extractor import extract_filters
from app.retrieval.bm25_index import BM25Index
from app.retrieval.fusion import reciprocal_rank_fusion
from app.vectorstore.factory import get_vector_store
from app.vectorstore.collections import collection_for
from app.embeddings.factory import get_embedding_provider
from app.repositories.chunk_repository import ChunkRepository
from app.models.search import SearchLog
from app.core.logging_config import logger

class RetrievalService:
    def __init__(self, db):
        self.db = db
        self.store = get_vector_store()
        self.chunk_repo = ChunkRepository(db)

    async def hybrid_search(self, raw_query: str, top_k: int = 10, filters: dict | None = None,
                              user_id: str | None = None, use_rewrite: bool = True) -> list[dict]:
        t0 = time.perf_counter()

        query = normalize_query(raw_query)
        query = resolve_acronyms(query)
        rewritten = await rewrite_query(query) if use_rewrite else query

        auto_filters = extract_filters(raw_query)
        combined_filters = {**auto_filters, **(filters or {})}

        # --- Dense retrieval ---
        provider = get_embedding_provider()
        query_vector = (await provider.embed([rewritten]))[0]
        dense_results = await self.store.search(collection_for("text"), query_vector, top_k * 3, combined_filters)
        dense_ranked = [r["payload"]["chunk_id"] for r in dense_results if r["payload"].get("chunk_id")]
        dense_scores = {r["payload"]["chunk_id"]: r["score"] for r in dense_results if r["payload"].get("chunk_id")}

        # --- Sparse retrieval (BM25 over the same candidate pool for scale) ---
        candidate_chunk_ids = dense_ranked
        candidate_chunks = [c for c in await self._get_chunks(candidate_chunk_ids)]
        bm25 = BM25Index([c.id for c in candidate_chunks], [c.content for c in candidate_chunks])
        bm25_variants_scores = {}
        for variant in expand_query(query)[:3]:  # cap expansion fanout
            for cid, score in bm25.search(variant, top_k * 3):
                bm25_variants_scores[cid] = max(bm25_variants_scores.get(cid, 0), score)
        sparse_ranked = sorted(bm25_variants_scores, key=bm25_variants_scores.get, reverse=True)

        # --- Fusion ---
        fused = reciprocal_rank_fusion([dense_ranked, sparse_ranked])
        top_ids = sorted(fused, key=fused.get, reverse=True)[:top_k]

        # --- Context assembly ---
        chunk_map = {c.id: c for c in candidate_chunks}
        results = []
        for cid in top_ids:
            chunk = chunk_map.get(cid)
            if not chunk:
                continue
            results.append({
                "chunk_id": chunk.id, "document_id": chunk.document_id, "content": chunk.content,
                "pages": chunk.pages, "section_name": chunk.section_name,
                "fused_score": fused[cid], "dense_score": dense_scores.get(cid),
                "sparse_score": bm25_variants_scores.get(cid),
                "retrieval_method": "hybrid",
            })

        latency_ms = (time.perf_counter() - t0) * 1000
        self.db.add(SearchLog(user_id=user_id, query=raw_query, rewritten_query=rewritten,
                                filters=combined_filters, result_count=len(results), latency_ms=latency_ms))
        await self.db.commit()

        logger.info("hybrid_search_completed", query=raw_query, results=len(results), latency_ms=latency_ms)
        return results

    async def semantic_search(self, query: str, top_k: int = 10, filters: dict | None = None) -> list[dict]:
        provider = get_embedding_provider()
        vector = (await provider.embed([query]))[0]
        results = await self.store.search(collection_for("text"), vector, top_k, filters)
        return [{"chunk_id": r["payload"].get("chunk_id"), "score": r["score"], "payload": r["payload"]} for r in results]

    async def keyword_search(self, query: str, document_id: str, top_k: int = 10) -> list[dict]:
        chunks = await self.chunk_repo.get_for_document(document_id)
        bm25 = BM25Index([c.id for c in chunks], [c.content for c in chunks])
        ranked = bm25.search(query, top_k)
        chunk_map = {c.id: c for c in chunks}
        return [{"chunk_id": cid, "score": score, "content": chunk_map[cid].content} for cid, score in ranked]

    async def _get_chunks(self, chunk_ids: list[str]):
        from sqlalchemy import select
        from app.models.chunk import Chunk
        if not chunk_ids:
            return []
        result = await self.db.execute(select(Chunk).where(Chunk.id.in_(chunk_ids)))
        return result.scalars().all()