
# ===== app/api/v1/router.py (UPDATE) =====
from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.documents import router as documents_router
from app.api.v1.classification import router as classification_router
from app.api.v1.parsing import router as parsing_router
from app.api.v1.canonical import router as canonical_router
from app.api.v1.audit import router as audit_router

from app.api.v1.metadata import router as metadata_router
from app.api.v1.extraction import router as extraction_router
from app.api.v1.chunks import router as chunks_router
from app.api.v1.embeddings import router as embeddings_router
from app.api.v1.vectorstore import router as vectorstore_router
from app.api.v1.retrieval import router as retrieval_router
from app.api.v1.reranking import router as reranking_router
from app.api.v1.chat import router as chat_router
from app.api.v1.viewer import router as viewer_router
from app.api.v1.rule_engine import router as rule_engine_router

from app.api.v1.evaluation import router as evaluation_router
from app.api.v1.monitoring import router as monitoring_router

from app.api.v1.search_ui import router as search_ui_router



api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router)
api_router.include_router(audit_router)
api_router.include_router(retrieval_router)
api_router.include_router(users_router)
api_router.include_router(dashboard_router)
api_router.include_router(metadata_router)

api_router.include_router(documents_router)
api_router.include_router(classification_router)
api_router.include_router(parsing_router)
api_router.include_router(canonical_router)
api_router.include_router(extraction_router)
api_router.include_router(chunks_router)
api_router.include_router(embeddings_router)
api_router.include_router(vectorstore_router)
api_router.include_router(reranking_router)
api_router.include_router(viewer_router)

api_router.include_router(rule_engine_router)

api_router.include_router(search_ui_router)

api_router.include_router(chat_router)
api_router.include_router(evaluation_router)

api_router.include_router(monitoring_router)