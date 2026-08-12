# ===== app/models/classification.py =====
from sqlalchemy import String, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel

class Classification(BaseModel):
    __tablename__ = "classifications"
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    document_type: Mapped[str] = mapped_column(String)
    confidence: Mapped[float] = mapped_column(Float)
    method: Mapped[str] = mapped_column(String)  # rule_based | ai_based | hybrid | manual
    model_version: Mapped[str] = mapped_column(String, nullable=True)
    pipeline: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="completed")  # completed | needs_review | failed
