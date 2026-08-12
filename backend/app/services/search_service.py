
# ===== app/services/search_service.py =====
"""Pure semantic search — hybrid (BM25) fusion and reranking come in Phase 13."""
from app.vectorstore.factory import get_vector_store
from app.vectorstore.collections import collection_for
from app.embeddings.factory import get_embedding_provider

class SearchService:
    def __init__(self, db):
        self.db = db
        self.store = get_vector_store()

    async def search(self, query: str, embedding_type: str = "text", top_k: int = 10,
                      filters: dict | None = None, provider_name: str | None = None) -> list[dict]:
        provider = get_embedding_provider(provider_name)
        query_vector = (await provider.embed([query]))[0]
        collection = collection_for(embedding_type)
        return await self.store.search(collection, query_vector, top_k, filters)

    async def get_similar_chunks(self, chunk_id: str, chunk_vector: list[float], top_k: int = 5) -> list[dict]:
        results = await self.store.search(collection_for("text"), chunk_vector, top_k + 1)
        return [r for r in results if r["payload"].get("chunk_id") != chunk_id][:top_k]

    async def collection_stats(self) -> dict:
        from app.vectorstore.collections import COLLECTIONS
        stats = {}
        for etype, name in COLLECTIONS.items():
            stats[etype] = await self.store.get_collection_stats(name)
        return stats