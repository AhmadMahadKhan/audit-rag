# ===== app/models/search_management.py =====
from sqlalchemy import String, ForeignKey, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel

class SavedSearch(BaseModel):
    __tablename__ = "saved_searches"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String)
    query: Mapped[str] = mapped_column(String)
    filters: Mapped[dict] = mapped_column(JSON, default=dict)
    search_mode: Mapped[str] = mapped_column(String, default="hybrid")
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)


