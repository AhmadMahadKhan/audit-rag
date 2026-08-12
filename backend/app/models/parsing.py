
# ===== app/models/parsing.py =====
from sqlalchemy import String, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel

class ParsingResult(BaseModel):
    __tablename__ = "parsing_results"
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    parser_name: Mapped[str] = mapped_column(String)
    parser_version: Mapped[str] = mapped_column(String)
    ocr_used: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String, default="completed")  # completed | failed | needs_review
    error_message: Mapped[str] = mapped_column(String, nullable=True)
    processing_time_ms: Mapped[float] = mapped_column(Float, nullable=True)
    raw_text: Mapped[str] = mapped_column(String, nullable=True)
    parsed_json: Mapped[dict] = mapped_column(JSON)  # full ParsedDocument.model_dump()
