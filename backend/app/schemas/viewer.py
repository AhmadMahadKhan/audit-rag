# ===== app/schemas/viewer.py =====
from pydantic import BaseModel

class DocumentViewerBundle(BaseModel):
    """Single aggregated payload so the frontend viewer loads everything in one request."""
    document: dict
    classification: dict | None
    parsing: dict | None
    canonical_summary: dict | None
    metadata: list[dict]
    entities: list[dict]
    facts: list[dict]
    line_items: list[dict]
    chunks: list[dict]
    embedding_status: dict

class BoundingBoxOut(BaseModel):
    block_id: str
    page: int
    x: float
    y: float
    width: float
    height: float
    type: str
    text: str
    confidence: float | None

class CitationResolveOut(BaseModel):
    document_id: str
    chunk_id: str | None
    page: int | None
    section_name: str | None
    bbox: dict | None
    content: str | None

class DocumentSearchHit(BaseModel):
    block_id: str
    page: int
    text: str
    match_start: int
    match_end: int