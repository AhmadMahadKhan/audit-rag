# ===== app/models/vector_sync.py =====
from sqlalchemy import String, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel

class VectorSyncStatus(BaseModel):
    """Tracks Postgres <-> Qdrant sync per embedding record — enables retry
    and consistency checks without scanning Qdrant directly."""
    __tablename__ = "vector_sync_status"
    embedding_id: Mapped[str] = mapped_column(ForeignKey("embedding_records.id"), index=True)
    collection: Mapped[str] = mapped_column(String)
    point_id: Mapped[str] = mapped_column(String)
    synced: Mapped[bool] = mapped_column(Boolean, default=False)
    error_message: Mapped[str] = mapped_column(String, nullable=True)
    retry_count: Mapped[int] = mapped_column(default=0)
