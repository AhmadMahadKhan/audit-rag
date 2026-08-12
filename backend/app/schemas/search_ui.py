# ===== app/schemas/search_ui.py =====
from pydantic import BaseModel
from datetime import datetime

class SearchUIRequest(BaseModel):
    query: str
    mode: str = "hybrid"  # hybrid | semantic | keyword | entity | fact | metadata
    filters: dict | None = None
    top_k: int = 20

class SearchResultOut(BaseModel):
    document_id: str
    document_title: str | None = None
    chunk_id: str | None = None
    snippet: str | None = None
    page: int | None = None
    section_name: str | None = None
    hybrid_score: float | None = None
    rerank_score: float | None = None
    final_score: float | None = None

class SearchHistoryOut(BaseModel):
    id: str
    query: str
    filters: dict
    result_count: int
    created_at: datetime

    class Config:
        from_attributes = True

class SavedSearchOut(BaseModel):
    id: str
    name: str
    query: str
    filters: dict
    search_mode: str
    is_favorite: bool
    created_at: datetime

    class Config:
        from_attributes = True

class SaveSearchRequest(BaseModel):
    name: str
    query: str
    filters: dict = {}
    search_mode: str = "hybrid"
