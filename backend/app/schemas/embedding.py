
# ===== app/schemas/embedding.py =====
from pydantic import BaseModel
from datetime import datetime

class EmbeddingRecordOut(BaseModel):
    id: str
    embedding_type: str
    model_name: str
    model_version: str
    vector_dimension: int
    status: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class EmbeddingRunOut(BaseModel):
    id: str
    document_id: str
    model_name: str
    embedding_types: list[str]
    total_count: int
    failed_count: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class GenerateEmbeddingsRequest(BaseModel):
    types: list[str] | None = None
    provider: str | None = None