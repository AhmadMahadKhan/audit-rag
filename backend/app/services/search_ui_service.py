# ===== app/services/search_ui_service.py =====
"""Orchestrates the full 'discovery' experience: mode routing, result
formatting, suggestions, and the history/saved-search side features. Reuses
RetrievalService/RerankingService — no retrieval logic duplicated here."""
from app.services.reranking_service import RerankingService
from app.services.retrieval_service import RetrievalService
from app.repositories.knowledge_repository import KnowledgeRepository
from app.repositories.metadata_repository import MetadataRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.search_management_repository import SearchManagementRepository
from app.search_ui.formatter import format_result
from app.models.search_management import SavedSearch
from app.core.exceptions import DocumentNotFound

class SearchUIService:
    def __init__(self, db):
        self.db = db
        self.reranking = RerankingService(db)
        self.retrieval = RetrievalService(db)
        self.knowledge_repo = KnowledgeRepository(db)
        self.metadata_repo = MetadataRepository(db)
        self.doc_repo = DocumentRepository(db)
        self.mgmt_repo = SearchManagementRepository(db)

    async def search(self, query: str, mode: str, filters: dict | None, user_id: str, top_k: int = 20) -> list[dict]:
        if mode == "hybrid":
            rerank_result = await self.reranking.retrieve_and_rerank(query, top_n=top_k, filters=filters, user_id=user_id)
            raw_results = rerank_result["results"]
        elif mode in ("bm25", "keyword"):
            # Fast BM25 keyword search over DB chunks
            from app.models.chunk import Chunk
            recent_chunks = await self.doc_repo.db.execute(
                __import__("sqlalchemy").select(Chunk).limit(100)
            )
            chunks = recent_chunks.scalars().all()
            if not chunks:
                raw_results = []
            else:
                from app.retrieval.bm25_index import BM25Index
                bm25 = BM25Index([c.id for c in chunks], [c.content for c in chunks])
                scored_ids = bm25.search(query, top_k)
                chunk_map = {c.id: c for c in chunks}
                raw_results = []
                for cid, score in scored_ids:
                    c = chunk_map.get(cid)
                    if c:
                        raw_results.append({
                            "chunk_id": c.id,
                            "document_id": c.document_id,
                            "content": c.content,
                            "pages": c.pages,
                            "section_name": c.section_name,
                            "fused_score": score
                        })
        elif mode == "semantic":
            raw_results = await self.retrieval.hybrid_search(query, top_k, filters, user_id=user_id)
        elif mode == "entity":
            entities = await self.knowledge_repo.search_entities(None, query, limit=top_k)
            return [{"document_id": e.document_id, "entity_type": e.entity_type, "value": e.value,
                     "confidence": e.confidence, "page": e.page} for e in entities]
        elif mode == "fact":
            facts = await self.knowledge_repo.search_facts(None, limit=top_k)
            facts = [f for f in facts if query.lower() in f.value.lower()]
            return [{"document_id": f.document_id, "fact_type": f.fact_type, "value": f.value,
                     "confidence": f.confidence, "status": f.status} for f in facts]
        elif mode == "metadata":
            doc_ids = await self.metadata_repo.search({"vendor": query} if query else {}, limit=top_k)
            return [{"document_id": d} for d in doc_ids]
        else:
            raise ValueError(f"Unknown search mode: {mode}")

        # resolve document titles for display
        titles = {}
        formatted = []
        for item in raw_results:
            doc_id = item["document_id"]
            if doc_id not in titles:
                doc = await self.doc_repo.get_by_id(doc_id)
                titles[doc_id] = doc.original_filename if doc else "Unknown Document"
            formatted.append(format_result(item, query, titles[doc_id]))
        return formatted

    async def suggest(self, partial_query: str, user_id: str, limit: int = 5) -> list[str]:
        """Combines recent personal history + globally popular queries matching the prefix."""
        history = await self.mgmt_repo.get_recent_history(user_id, limit=50)
        popular = await self.mgmt_repo.get_popular_queries(limit=20)

        candidates = {h.query for h in history} | {q for q, _ in popular}
        matches = [c for c in candidates if c.lower().startswith(partial_query.lower())]
        return matches[:limit]

    async def save_search(self, user_id: str, name: str, query: str, filters: dict, mode: str) -> SavedSearch:
        saved = SavedSearch(user_id=user_id, name=name, query=query, filters=filters, search_mode=mode)
        return await self.mgmt_repo.create_saved_search(saved)

    async def run_saved_search(self, search_id: str, user_id: str) -> list[dict]:
        saved = await self.mgmt_repo.get_saved_search(search_id, user_id)
        if not saved:
            raise DocumentNotFound("Saved search not found")
        return await self.search(saved.query, saved.search_mode, saved.filters, user_id)
