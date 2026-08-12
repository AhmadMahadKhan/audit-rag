# ===== app/models/embedding.py =====
from sqlalchemy import String, Integer, ForeignKey, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel

class EmbeddingRecord(BaseModel):
    __tablename__ = "embedding_records"
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    chunk_id: Mapped[str] = mapped_column(String, nullable=True, index=True)  # null for doc-level (summary) embeddings
    source_ref_id: Mapped[str] = mapped_column(String, nullable=True)  # entity_id / metadata_key / table_id depending on type
    embedding_type: Mapped[str] = mapped_column(String, index=True)  # text | summary | metadata | entity | table
    model_name: Mapped[str] = mapped_column(String)
    model_version: Mapped[str] = mapped_column(String)
    vector_dimension: Mapped[int] = mapped_column(Integer)
    vector: Mapped[list] = mapped_column(JSON)  # stored here until Phase 12 moves it to Qdrant
    content_hash: Mapped[str] = mapped_column(String, index=True)  # dedupe key
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)  # False = superseded by re-index
    status: Mapped[str] = mapped_column(String, default="valid")  # valid | invalid | failed
    error_message: Mapped[str] = mapped_column(String, nullable=True)

class EmbeddingRun(BaseModel):
    __tablename__ = "embedding_runs"
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    model_name: Mapped[str] = mapped_column(String)
    embedding_types: Mapped[list] = mapped_column(JSON)
    total_count: Mapped[int] = mapped_column(default=0)
    failed_count: Mapped[int] = mapped_column(default=0)
    status: Mapped[str] = mapped_column(String, default="completed")