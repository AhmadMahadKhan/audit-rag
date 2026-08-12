# ===== app/models/document.py =====
from sqlalchemy import String, Integer, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel
import enum

class UploadStatus(str, enum.Enum):
    QUEUED = "queued"
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    VALIDATING = "validating"
    STORED = "stored"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Document(BaseModel):
    __tablename__ = "documents"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    original_filename: Mapped[str] = mapped_column(String)
    storage_filename: Mapped[str] = mapped_column(String)
    storage_path: Mapped[str] = mapped_column(String)
    storage_provider: Mapped[str] = mapped_column(String, default="local")
    file_size: Mapped[int] = mapped_column(Integer)
    mime_type: Mapped[str] = mapped_column(String)
    file_extension: Mapped[str] = mapped_column(String)
    file_hash: Mapped[str] = mapped_column(String, index=True)
    status: Mapped[str] = mapped_column(SAEnum(UploadStatus), default=UploadStatus.QUEUED)
    error_message: Mapped[str] = mapped_column(String, nullable=True)
    processing_status: Mapped[str] = mapped_column(String, default="not_started")  # for later phases
    document_type: Mapped[str] = mapped_column(String, nullable=True)  # denormalized latest classification
