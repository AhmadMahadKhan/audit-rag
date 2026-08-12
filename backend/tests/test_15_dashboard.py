# ===== tests/test_15_dashboard.py =====
"""Phase 3 — Dashboard aggregation endpoints."""
import pytest

pytestmark = pytest.mark.asyncio


class TestDashboard:
    async def test_summary_returns_all_cards(self, client, admin_headers):
        resp = await client.get("/api/v1/dashboard/summary", headers=admin_headers)
        assert resp.status_code == 200
        body = resp.json()
        for key in ("total_documents", "active_users", "embedding_count"):
            assert key in body

    async def test_activity_feed_populated_after_actions(self, client, user_headers, admin_headers, sample_invoice_bytes):
        files = {"files": ("dashboard-test.txt", sample_invoice_bytes, "text/plain")}
        await client.post("/api/v1/documents/upload", headers=user_headers, files=files)
        resp = await client.get("/api/v1/dashboard/activity", headers=admin_headers)
        assert resp.status_code == 200
        assert any(a["event_type"] == "document_uploaded" for a in resp.json())

    async def test_system_health_reports_service_statuses(self, client, admin_headers):
        resp = await client.get("/api/v1/dashboard/health", headers=admin_headers)
        assert resp.status_code == 200
        assert "services" in resp.json()
        assert resp.json()["overall"] in ("up", "degraded", "down")

    async def test_unprivileged_user_denied_dashboard_access(self, client, user_headers):
        resp = await client.get("/api/v1/dashboard/summary", headers=user_headers)
        assert resp.status_code == 403