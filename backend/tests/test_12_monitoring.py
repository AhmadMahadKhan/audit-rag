# ===== tests/test_12_monitoring.py =====
"""Phase 20 — Observability: redaction, error tracking, cost, health checks."""
import pytest

pytestmark = pytest.mark.asyncio


class TestRedaction:
    def test_redacts_password_field(self):
        from app.observability.redaction import redact_dict
        result = redact_dict({"username": "bob", "password": "secret123"})
        assert result["password"] == "***REDACTED***"
        assert result["username"] == "bob"

    def test_redacts_nested_token_field(self):
        from app.observability.redaction import redact_dict
        result = redact_dict({"auth": {"access_token": "abc.def.ghi"}})
        assert result["auth"]["access_token"] == "***REDACTED***"

    def test_truncates_long_text_fields(self):
        from app.observability.redaction import redact_dict
        result = redact_dict({"content": "x" * 3000})
        assert len(result["content"]) < 3000
        assert "truncated" in result["content"]

    def test_redact_text_masks_bearer_tokens(self):
        from app.observability.redaction import redact_text
        result = redact_text("Authorization: Bearer abc123.def456")
        assert "abc123" not in result
        assert "REDACTED" in result

    def test_redact_text_masks_ssn_pattern(self):
        from app.observability.redaction import redact_text
        result = redact_text("SSN: 123-45-6789")
        assert "123-45-6789" not in result


class TestCostTracker:
    def test_zero_cost_for_local_model(self, monkeypatch):
        from app.observability.cost_tracker import estimate_llm_cost
        from app.core.config import settings
        monkeypatch.setattr(settings, "LLM_INPUT_COST_PER_1K", 0.0)
        monkeypatch.setattr(settings, "LLM_OUTPUT_COST_PER_1K", 0.0)
        assert estimate_llm_cost(1000, 500) == 0.0

    def test_cost_scales_with_tokens(self, monkeypatch):
        from app.observability.cost_tracker import estimate_llm_cost
        from app.core.config import settings
        monkeypatch.setattr(settings, "LLM_INPUT_COST_PER_1K", 0.01)
        monkeypatch.setattr(settings, "LLM_OUTPUT_COST_PER_1K", 0.03)
        cost = estimate_llm_cost(2000, 1000)
        assert cost == pytest.approx(0.02 + 0.03)


class TestErrorTracker:
    def test_fingerprint_consistent_for_same_error(self):
        from app.observability.error_tracker import make_fingerprint
        f1 = make_fingerprint("ValueError", "bad input")
        f2 = make_fingerprint("ValueError", "bad input")
        assert f1 == f2

    def test_fingerprint_differs_for_different_errors(self):
        from app.observability.error_tracker import make_fingerprint
        f1 = make_fingerprint("ValueError", "bad input")
        f2 = make_fingerprint("KeyError", "missing key")
        assert f1 != f2

    def test_classify_known_exception(self):
        from app.observability.error_tracker import classify_exception
        from app.core.exceptions import AuthenticationError
        assert classify_exception(AuthenticationError("x")) == "authentication"

    def test_classify_unknown_exception_defaults_internal(self):
        from app.observability.error_tracker import classify_exception
        assert classify_exception(RuntimeError("x")) == "internal"

    async def test_repeated_error_increments_occurrence_count(self, db_session):
        from app.observability.error_tracker import track_error
        try:
            raise ValueError("consistent error message")
        except ValueError as e:
            await track_error(db_session, e, service="test")
            await track_error(db_session, e, service="test")

        from sqlalchemy import select
        from app.models.monitoring import ErrorEvent
        result = await db_session.execute(select(ErrorEvent))
        events = result.scalars().all()
        assert len(events) == 1
        assert events[0].occurrence_count == 2


class TestAlertEvaluator:
    async def test_alert_fires_when_threshold_exceeded(self, db_session):
        from app.models.monitoring import AlertRule
        from app.observability.alert_evaluator import AlertEvaluator
        db_session.add(AlertRule(name="high_latency", metric_name="p95_latency_ms",
                                   condition="gt", threshold=1000, severity="high"))
        await db_session.commit()

        fired = await AlertEvaluator(db_session).evaluate({"p95_latency_ms": 1500})
        assert len(fired) == 1
        assert fired[0].severity == "high"

    async def test_alert_does_not_fire_below_threshold(self, db_session):
        from app.models.monitoring import AlertRule
        from app.observability.alert_evaluator import AlertEvaluator
        db_session.add(AlertRule(name="high_latency2", metric_name="p95_latency_ms",
                                   condition="gt", threshold=1000, severity="high"))
        await db_session.commit()

        fired = await AlertEvaluator(db_session).evaluate({"p95_latency_ms": 200})
        assert len(fired) == 0

    def test_check_condition_operators(self):
        from app.observability.alert_evaluator import check_condition
        assert check_condition(10, "gt", 5) is True
        assert check_condition(3, "lt", 5) is True
        assert check_condition(5, "eq", 5) is True
        assert check_condition(5, "gt", 10) is False


class TestHealthEndpoints:
    async def test_health_endpoint(self, client):
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    async def test_liveness_endpoint(self, client):
        resp = await client.get("/api/v1/health/live")
        assert resp.status_code == 200

    async def test_readiness_endpoint_reports_dependency_status(self, client):
        resp = await client.get("/api/v1/health/ready")
        assert resp.status_code == 200
        body = resp.json()
        assert "checks" in body
        assert "database" in body["checks"]


class TestPrometheusMetricsEndpoint:
    async def test_metrics_endpoint_returns_prometheus_format(self, client):
        resp = await client.get("/api/v1/monitoring/metrics")
        assert resp.status_code == 200
        assert "text/plain" in resp.headers["content-type"]