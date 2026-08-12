
# ===== app/schemas/retrieval.py =====
from pydantic import BaseModel

class SearchRequestIn(BaseModel):
    query: str
    top_k: int = 10
    filters: dict | None = None
    use_rewrite: bool = True

class ContextItem(BaseModel):
    chunk_id: str
    document_id: str
    content: str
    pages: list[int]
    section_name: str | None
    fused_score: float
    dense_score: float | None
    sparse_score: float | None
    retrieval_method: str