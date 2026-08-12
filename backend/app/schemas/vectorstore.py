# ===== app/schemas/vectorstore.py =====
from pydantic import BaseModel

class IndexResult(BaseModel):
    indexed: int
    failed: int
    collections: list[str]

class SearchRequest(BaseModel):
    query: str
    embedding_type: str = "text"
    top_k: int = 10
    filters: dict | None = None

class SearchResultItem(BaseModel):
    id: str
    score: float
    payload: dict

class CollectionStats(BaseModel):
    vectors_count: int
    points_count: int
    status: str
    segments_count: int | None = None