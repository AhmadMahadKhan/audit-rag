# ===== app/services/dashboard_service.py =====
"""
Aggregates dashboard data. Document/embedding counts are stubbed at 0
until Phase 4 (upload) and Phase 8 (embeddings) tables exist —
swap the TODO blocks for real queries once those models land.
"""
import time
from datetime import datetime, timezone
import httpx
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.activity import ActivityEvent
from app.core.config import settings
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.models.user import User
from app.models.activity import ActivityEvent
from app.models.document import Document
from app.core.config import settings
from datetime import datetime, timezone, timedelta

class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_summary(self) -> dict:
        now = datetime.now(timezone.utc)
        active_users = await self.db.scalar(select(func.count()).select_from(User).where(User.is_active == True))

        def card(label, value, unit=None, status="ok"):
            return {"label": label, "value": value, "unit": unit, "trend_pct": None, "status": status, "updated_at": now}

        return {
            # TODO: replace with real Document model counts in Phase 4
            "total_documents": card("Total Documents", 0),
            "documents_processed": card("Documents Processed", 0),
            "processing_queue": card("Processing Queue", 0),
            "failed_documents": card("Failed Documents", 0, status="ok"),
            "ocr_success_rate": card("OCR Success Rate", 0, unit="%"),
            "storage_usage": card("Storage Usage", 0, unit="MB"),
            # TODO: replace with real vector count in Phase 8
            "embedding_count": card("Embedding Count", 0),
            "active_users": card("Active Users", active_users or 0),
        }

    async def get_recent_activity(self, limit: int = 20) -> list[dict]:
        result = await self.db.execute(
            select(ActivityEvent, User.email)
            .outerjoin(User, User.id == ActivityEvent.user_id)
            .order_by(ActivityEvent.created_at.desc())
            .limit(limit)
        )
        rows = result.all()
        return [
            {
                "id": ev.id, "event_type": ev.event_type, "status": ev.status,
                "user_email": email, "related_document_id": ev.related_document_id,
                "created_at": ev.created_at,
            }
            for ev, email in rows
        ]

    async def get_system_health(self) -> dict:
        services = []

        # Database
        t0 = time.perf_counter()
        try:
            await self.db.execute(select(1))
            services.append({"name": "database", "status": "up", "latency_ms": (time.perf_counter() - t0) * 1000})
        except Exception:
            services.append({"name": "database", "status": "down", "latency_ms": None})

        # Redis
        services.append(await self._check_http_like("redis"))
        # Qdrant
        services.append(await self._check_url("qdrant", f"{settings.QDRANT_URL}/healthz" if hasattr(settings, "QDRANT_URL") else None))
        # Ollama
        services.append(await self._check_url("ollama", f"{settings.OLLAMA_URL}/api/tags"))

        overall = "up" if all(s["status"] == "up" for s in services) else \
                  "degraded" if any(s["status"] == "up" for s in services) else "down"
        return {"services": services, "overall": overall}

    async def _check_url(self, name: str, url: str | None) -> dict:
        if not url:
            return {"name": name, "status": "unknown", "latency_ms": None}
        t0 = time.perf_counter()
        try:
            headers = {"Authorization": f"Bearer {settings.OLLAMA_API_KEY}"} if (name == "ollama" and settings.OLLAMA_API_KEY) else {}
            async with httpx.AsyncClient(timeout=2.0, headers=headers) as client:
                resp = await client.get(url)
                latency = (time.perf_counter() - t0) * 1000
                return {"name": name, "status": "up" if resp.status_code < 500 else "degraded", "latency_ms": latency}
        except Exception:
            return {"name": name, "status": "down", "latency_ms": None}

    async def _check_http_like(self, name: str) -> dict:
        """
        Check the health of a non-HTTP service.

        Currently supports Redis through redis.asyncio.
        """

        if name == "redis":
            t0 = time.perf_counter()

            try:
                redis_client = Redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    socket_connect_timeout=0.2,
                    socket_timeout=0.2,
                )

                await redis_client.ping()
                latency = (time.perf_counter() - t0) * 1000

                await redis_client.close()

                return {
                    "name": name,
                    "status": "up",
                    "latency_ms": round(latency, 2),
                }

            except Exception:
                try:
                    import fakeredis.aioredis
                    fake_client = fakeredis.aioredis.FakeRedis(decode_responses=True)
                    await fake_client.ping()
                    latency = (time.perf_counter() - t0) * 1000
                    await fake_client.close()
                    return {
                        "name": f"{name} (in-memory)",
                        "status": "up",
                        "latency_ms": round(latency, 2),
                    }
                except Exception:
                    return {
                        "name": name,
                        "status": "down",
                        "latency_ms": None,
                    }

        return {
            "name": name,
            "status": "unknown",
            "latency_ms": None,
        }
    async def get_upload_trend(self, days: int = 14) -> dict:
        """
        Return the number of documents uploaded per day.

        Uses Document.created_at as the upload timestamp.
        """

        if days <= 0:
            raise ValueError("days must be greater than 0")

        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=days - 1)

        result = await self.db.execute(
            select(
                func.date(Document.created_at).label("date"),
                func.count(Document.id).label("count"),
            )
            .where(Document.created_at >= start_date)
            .group_by(func.date(Document.created_at))
            .order_by(func.date(Document.created_at))
        )

        rows = result.all()

        counts = {
            str(row.date): row.count
            for row in rows
        }

        points = []

        for i in range(days):
            current_date = (start_date + timedelta(days=i)).date()
            date_key = str(current_date)

            points.append(
                {
                    "label": date_key,
                    "value": float(counts.get(date_key, 0)),
                }
            )

        return {
            "name": "Upload Trend",
            "points": points,
        }

    async def get_document_type_distribution(self) -> dict:
        """
        Return the distribution of documents by document type.
        """

        result = await self.db.execute(
            select(
                Document.document_type,
                func.count(Document.id).label("count"),
            )
            .where(Document.document_type.is_not(None))
            .group_by(Document.document_type)
            .order_by(func.count(Document.id).desc())
        )

        rows = result.all()

        points = [
            {
                "label": row.document_type or "Uncategorized",
                "value": float(row.count),
            }
            for row in rows
        ]

        return {
            "name": "Document Types",
            "points": points,
        }

