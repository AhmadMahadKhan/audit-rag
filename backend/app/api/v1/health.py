# ===== app/api/v1/health.py  =====
import httpx
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.config import settings

router = APIRouter()

@router.get("/health")
async def health():
    return {"status": "ok"}

@router.get("/health/live")
async def live():
    return {"status": "alive"}

@router.get("/health/ready")
async def ready(db: AsyncSession = Depends(get_db)):
    checks = {}

    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "up"
    except Exception as e:
        checks["database"] = f"down: {e}"

    try:
        headers = {"api-key": settings.QDRANT_API_KEY} if settings.QDRANT_API_KEY else {}
        async with httpx.AsyncClient(timeout=2.0, headers=headers) as client:
            resp = await client.get(f"{settings.QDRANT_URL}/healthz")
            checks["qdrant"] = "up" if resp.status_code < 500 else "degraded"
    except Exception:
        checks["qdrant"] = "down"

    try:
        headers = {"Authorization": f"Bearer {settings.OLLAMA_API_KEY}"} if settings.OLLAMA_API_KEY else {}
        async with httpx.AsyncClient(timeout=2.0, headers=headers) as client:
            resp = await client.get(f"{settings.OLLAMA_URL}/api/tags")
            checks["llm_provider"] = "up" if resp.status_code < 500 else "degraded"
    except Exception:
        checks["llm_provider"] = "down"

    overall = "ready" if all(v == "up" for v in checks.values()) else "not_ready"
    return {"status": overall, "checks": checks}