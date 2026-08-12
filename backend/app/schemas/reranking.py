# ===== app/schemas/reranking.py =====
from pydantic import BaseModel

class RerankRequest(BaseModel):
    query: str
    top_n: int | None = None
    filters: dict | None = None
    provider: str | None = None

class RerankedItem(BaseModel):
    chunk_id: str
    document_id: str
    content: str
    pages: list[int]
    section_name: str | None
    fused_score: float
    rerank_score: float | None = None
    final_score: float | None = None
    retrieval_method: str

class RerankResponse(BaseModel):
    results: list[RerankedItem]
    fallback_used: bool
    latency_ms: float
    candidates_considered: int = 0