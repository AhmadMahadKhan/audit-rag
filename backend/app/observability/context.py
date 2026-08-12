
# ===== app/observability/context.py =====
"""Binds request_id/trace_id/user_id into every log line for the duration of
a request — implements the 'every important log should include...' spec."""
import structlog
from contextvars import ContextVar

current_trace_id: ContextVar[str] = ContextVar("trace_id", default="")

def bind_request_context(request_id: str, user_id: str | None = None, trace_id: str | None = None):
    structlog.contextvars.bind_contextvars(
        request_id=request_id, user_id=user_id or "anonymous", trace_id=trace_id or request_id,
    )

def clear_request_context():
    structlog.contextvars.clear_contextvars()
