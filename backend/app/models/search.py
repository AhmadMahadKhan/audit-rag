# ===== app/models/search.py =====
from sqlalchemy import String, Float, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel

class SearchLog(BaseModel):
    __tablename__ = "search_logs"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=True)
    query: Mapped[str] = mapped_column(String)
    rewritten_query: Mapped[str] = mapped_column(String, nullable=True)
    filters: Mapped[dict] = mapped_column(JSON, default=dict)
    result_count: Mapped[int] = mapped_column(default=0)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=True)
