# ===== app/schemas/chunk.py =====
from pydantic import BaseModel
from datetime import datetime

class ChunkOut(BaseModel):
    id: str
    chunk_index: int
    chunk_type: str
    content: str
    section_name: str | None
    pages: list[int]
    heading_path: list[str]
    token_count: int
    prev_chunk_id: str | None
    next_chunk_id: str | None
    validation_status: str

    class Config:
        from_attributes = True

class ChunkingRunOut(BaseModel):
    id: str
    document_id: str
    chunker_used: str
    chunk_count: int
    invalid_chunk_count: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
