from sqlalchemy import String, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel

class CanonicalDocumentRecord(BaseModel):
    __tablename__ = "canonical_documents"
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    schema_version: Mapped[str] = mapped_column(String)
    validation_status: Mapped[str] = mapped_column(String, default="valid")
    validation_issues: Mapped[list] = mapped_column(JSON, default=list)
    canonical_json: Mapped[dict] = mapped_column(JSON)
