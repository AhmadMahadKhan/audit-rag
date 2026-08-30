
# ===== app/services/search_service.py =====
"""Pure semantic search — hybrid (BM25) fusion and reranking come in Phase 13."""
from app.vectorstore.factory import get_vector_store
from app.vectorstore.collections import collection_for
from app.embeddings.factory import get_embedding_provider
from app.core.logging_config import logger

class SearchService:
    def __init__(self, db):
        self.db = db
        self.store = get_vector_store()

    async def search(
        self,
        collection: str,
        vector: list[float],
        top_k: int,
        filters: dict | None = None,
    ) -> list[dict]:

        if not vector:
            logger.warning(
                "qdrant_search_empty_vector",
                collection=collection,
            )
            return []

        try:
            logger.info(
                "qdrant_search_start",
                collection=collection,
                vector_dimension=len(vector),
                top_k=top_k,
                filters=filters,
            )

            # Verify collection before searching
            info = await self.client.get_collection(collection)

            logger.info(
                "qdrant_collection_info",
                collection=collection,
                points_count=info.points_count,
                vectors_count=info.vectors_count,
                status=str(info.status),
            )

            qdrant_filter = (
                self._build_filter(filters)
                if filters
                else None
            )

            results = await self.client.query_points(
                collection_name=collection,
                query=vector,
                limit=top_k,
                query_filter=qdrant_filter,
                with_payload=True,
            )

            logger.info(
                "qdrant_search_success",
                collection=collection,
                results_count=len(results.points),
            )

            return [
                {
                    "id": p.id,
                    "score": p.score,
                    "payload": p.payload,
                }
                for p in results.points
            ]

        except Exception as e:
            logger.exception(
                "qdrant_search_failed",
                collection=collection,
                error=str(e),
            )
            raise

    async def get_similar_chunks(self, chunk_id: str, chunk_vector: list[float], top_k: int = 5) -> list[dict]:
        results = await self.store.search(collection_for("text"), chunk_vector, top_k + 1)
        return [r for r in results if r["payload"].get("chunk_id") != chunk_id][:top_k]

    async def collection_stats(self) -> dict:
        from app.vectorstore.collections import COLLECTIONS
        stats = {}
        for etype, name in COLLECTIONS.items():
            stats[etype] = await self.store.get_collection_stats(name)
        return stats