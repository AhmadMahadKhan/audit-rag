# ===== app/retrieval/bm25_index.py =====
"""In-memory BM25 index built from stored chunks. Rebuilt/cached per request
scope is too slow at scale — see note in service on caching strategy."""
from rank_bm25 import BM25Okapi

class BM25Index:
    def __init__(self, chunk_ids: list[str], texts: list[str]):
        self.chunk_ids = chunk_ids
        self.tokenized = [t.lower().split() for t in texts]
        self.bm25 = BM25Okapi(self.tokenized) if self.tokenized else None

    def search(self, query: str, top_k: int = 10) -> list[tuple[str, float]]:
        if not self.bm25:
            return []
        scores = self.bm25.get_scores(query.lower().split())
        ranked = sorted(zip(self.chunk_ids, scores), key=lambda x: x[1], reverse=True)
        return [(cid, score) for cid, score in ranked[:top_k] if score > 0]
