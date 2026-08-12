
# ===== app/middleware/logging.py (REPLACE — extends Phase 1's version) =====
import time
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging_config import logger
from app.observability.context import bind_request_context, clear_request_context
from app.observability.metrics import API_REQUEST_COUNT, API_REQUEST_LATENCY

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = getattr(request.state, "request_id", "unknown")
        bind_request_context(request_id)
        t0 = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            clear_request_context()
        duration = time.perf_counter() - t0

        API_REQUEST_COUNT.labels(method=request.method, path=request.url.path,
                                   status=response.status_code).inc()
        API_REQUEST_LATENCY.labels(method=request.method, path=request.url.path).observe(duration)

        logger.info("request", path=request.url.path, method=request.method,
                     status=response.status_code, duration_ms=duration * 1000, request_id=request_id)
        return response