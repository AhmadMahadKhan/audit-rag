from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.core.config import settings
from app.core.logging_config import logger
from app.core.exceptions import ApplicationError
from app.middleware.exception_handlers import application_exception_handler, unhandled_exception_handler
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.timing import TimingMiddleware
from app.middleware.logging import LoggingMiddleware
from app.api.v1.router import api_router
from app.observability.tracing import setup_tracing
app = FastAPI(title=settings.app_name)
tracer = setup_tracing(app)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.add_middleware(GZipMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(TimingMiddleware)
app.add_middleware(RequestIDMiddleware)

app.add_exception_handler(ApplicationError, application_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(api_router)

@app.on_event("startup")
async def startup():
    logger.info("startup", app=settings.app_name, env=settings.ENVIROMENT)