# ===== app/schemas/chat.py =====
from pydantic import BaseModel
from datetime import datetime

class ConversationOut(BaseModel):
    id: str
    title: str
    scratchpad_notes: str | None = None
    active_document_ids: list[str] | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    citations: list[dict]
    confidence: float | None
    validation_status: str
    created_at: datetime

    class Config:
        from_attributes = True

class SendMessageRequest(BaseModel):
    question: str
    filters: dict | None = None
    document_ids: list[str] | None = None   # NEW
    provider: str | None = None

class CreateConversationRequest(BaseModel):
    title: str | None = None