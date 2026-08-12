# ===== app/services/activity_logger.py =====
"""Call this from any service (upload, auth, chat) to record an activity event."""
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.activity import ActivityEvent

async def log_activity(db: AsyncSession, event_type: str, user_id: str | None = None,
                        status: str = "success", related_document_id: str | None = None,
                        detail: str | None = None):
    db.add(ActivityEvent(user_id=user_id, event_type=event_type, status=status,
                          related_document_id=related_document_id, detail=detail))
    await db.commit()