# ===== app/observability/error_tracker.py =====
"""Deduplicates errors by fingerprint (exception type + first line of
message) so the same recurring bug doesn't flood the table — implements
Phase 20's 'group repeated errors' requirement."""
import hashlib
import traceback
from sqlalchemy import select
from app.models.monitoring import ErrorEvent
from app.observability.metrics import ERROR_COUNT
from app.observability.redaction import redact_text

CATEGORY_MAP = {
    "AuthenticationError": "authentication", "AuthorizationError": "authorization",
    "ValidationFailed": "validation", "DocumentNotFound": "validation",
    "OCRFailed": "ocr", "StorageError": "storage", "RuleEngineError": "internal",
}

def classify_exception(exc: Exception) -> str:
    return CATEGORY_MAP.get(type(exc).__name__, "internal")

def make_fingerprint(exc_type: str, message: str) -> str:
    key = f"{exc_type}:{message.split(chr(10))[0][:100]}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]

async def track_error(db, exc: Exception, service: str | None = None, endpoint: str | None = None,
                        request_id: str | None = None, user_id: str | None = None):
    category = classify_exception(exc)
    message = redact_text(str(exc))
    fingerprint = make_fingerprint(type(exc).__name__, message)

    ERROR_COUNT.labels(category=category, exception_type=type(exc).__name__).inc()

    result = await db.execute(select(ErrorEvent).where(ErrorEvent.fingerprint == fingerprint))
    existing = result.scalar_one_or_none()
    if existing:
        existing.occurrence_count += 1
        existing.message = message
    else:
        db.add(ErrorEvent(
            exception_type=type(exc).__name__, message=message, category=category, service=service,
            endpoint=endpoint, request_id=request_id, user_id=user_id,
            stack_trace=redact_text(traceback.format_exc())[:5000], fingerprint=fingerprint,
        ))
    await db.commit()