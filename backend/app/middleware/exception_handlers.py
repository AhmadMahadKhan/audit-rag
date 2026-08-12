
# ===== app/middleware/exception_handlers.py  =====
import traceback
from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.exceptions import ApplicationError
from app.db.session import AsyncSessionLocal
from app.observability.error_tracker import track_error
from app.core.logging_config import logger


async def _safe_track_error(exc: Exception, endpoint: str | None, request_id: str | None):
    """Error tracking is best-effort observability — it must never be the
    reason a request fails or an error response gets swallowed."""
    try:
        async with AsyncSessionLocal() as db:
            await track_error(db, exc, endpoint=endpoint, request_id=request_id)
    except Exception as tracking_error:
        logger.error("error_tracking_failed", original_error=str(exc), tracking_error=str(tracking_error))


async def application_exception_handler(request: Request, exc: ApplicationError):
    await _safe_track_error(exc, request.url.path, getattr(request.state, "request_id", None))
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": {"type": exc.__class__.__name__, "message": exc.message}},
    )


async def unhandled_exception_handler(request: Request, exc: Exception):
    traceback.print_exc()
    await _safe_track_error(exc, request.url.path, getattr(request.state, "request_id", None))
    return JSONResponse(status_code=500, content={
        "success": False,
        "error": {"type": "InternalServerError", "message": "An unexpected error occurred."},
    })