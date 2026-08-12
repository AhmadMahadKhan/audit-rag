# ===== app/models/chat.py =====
from sqlalchemy import String, ForeignKey, JSON, Float
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel

class Conversation(BaseModel):
    __tablename__ = "conversations"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String, default="New Conversation")

class Message(BaseModel):
    __tablename__ = "messages"
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"), index=True)
    role: Mapped[str] = mapped_column(String)  # user | assistant
    content: Mapped[str] = mapped_column(String)
    citations: Mapped[list] = mapped_column(JSON, default=list)
    confidence: Mapped[float] = mapped_column(Float, nullable=True)
    validation_status: Mapped[str] = mapped_column(String, default="valid")  # valid | low_confidence | refused
    token_count: Mapped[int] = mapped_column(nullable=True)
