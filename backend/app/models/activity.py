# ===== app/models/activity.py =====
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel

class ActivityEvent(BaseModel):
    __tablename__ = "activity_events"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=True)
    event_type: Mapped[str] = mapped_column(String)  # document_uploaded, ocr_completed, etc.
    status: Mapped[str] = mapped_column(String, default="success")
    related_document_id: Mapped[str] = mapped_column(String, nullable=True)
    detail: Mapped[str] = mapped_column(String, nullable=True)
