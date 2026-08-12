# ===== app/models/metadata.py =====
from sqlalchemy import String, Float, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel

class DocumentMetadata(BaseModel):
    __tablename__ = "document_metadata"
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    key: Mapped[str] = mapped_column(String, index=True)       # e.g. "vendor", "currency", "invoice_date"
    value: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String)              # document | business | financial | processing
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    extractor: Mapped[str] = mapped_column(String)
    extractor_version: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="valid")  # valid | needs_review | invalid

class MetadataExtractionRun(BaseModel):
    __tablename__ = "metadata_extraction_runs"
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    overall_confidence: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String, default="completed")
    field_count: Mapped[int] = mapped_column(default=0)
    low_confidence_count: Mapped[int] = mapped_column(default=0)