# ===== tests/test_06_rule_engine.py =====
"""Phase 18 — Rule Engine: unit tests on pure functions + integration via API."""
import uuid
import pytest
import pytest_asyncio

from app.rule_engine.base import RuleContext
from app.rule_engine.rules.financial_rules import (
    TotalEqualsSubtotalPlusTaxRule, NegativeInvoiceAmountRule, LineItemMathRule,
)
from app.rule_engine.rules.document_rules import MissingInvoiceNumberRule, EmptyDocumentRule
from app.rule_engine.risk_scoring import calculate_risk_score, score_to_level, route_for_level

pytestmark = pytest.mark.asyncio


def make_ctx(**overrides) -> RuleContext:
    base = dict(document_id="d1", document_type="invoice", canonical=None, metadata={},
                entities=[], facts={}, facts_raw=[], line_items=[], raw_text="", config={}, history={})
    base.update(overrides)
    return RuleContext(**base)


class TestFinancialRulesUnit:
    def test_total_equals_subtotal_plus_tax_passes(self):
        ctx = make_ctx(facts={"invoice_total": 165.0, "subtotal": 150.0, "tax_amount": 15.0})
        result = TotalEqualsSubtotalPlusTaxRule().evaluate(ctx)
        assert result.triggered is False

    def test_total_equals_subtotal_plus_tax_fails_on_mismatch(self):
        ctx = make_ctx(facts={"invoice_total": 999.0, "subtotal": 150.0, "tax_amount": 15.0})
        result = TotalEqualsSubtotalPlusTaxRule().evaluate(ctx)
        assert result.triggered is True
        assert result.severity == "high"

    def test_total_rule_skips_when_data_missing(self):
        ctx = make_ctx(facts={"invoice_total": 100.0})  # missing subtotal/tax
        result = TotalEqualsSubtotalPlusTaxRule().evaluate(ctx)
        assert result.triggered is False
        assert result.confidence == 0.0

    def test_negative_amount_detected(self):
        ctx = make_ctx(facts={"invoice_total": -50.0})
        result = NegativeInvoiceAmountRule().evaluate(ctx)
        assert result.triggered is True
        assert result.severity == "critical"

    def test_line_item_math_flags_mismatch(self):
        ctx = make_ctx(line_items=[{"item_name": "Widget", "quantity": 10, "unit_price": 5.0, "line_total": 999.0}])
        result = LineItemMathRule().evaluate(ctx)
        assert result.triggered is True
        assert len(result.evidence["mismatches"]) == 1

    def test_line_item_math_passes_correct_items(self):
        ctx = make_ctx(line_items=[{"item_name": "Widget", "quantity": 10, "unit_price": 5.0, "line_total": 50.0}])
        result = LineItemMathRule().evaluate(ctx)
        assert result.triggered is False


class TestDocumentRulesUnit:
    def test_missing_invoice_number_triggers_without_entity(self):
        ctx = make_ctx(entities=[])
        result = MissingInvoiceNumberRule().evaluate(ctx)
        assert result.triggered is True

    def test_missing_invoice_number_passes_with_entity(self):
        ctx = make_ctx(entities=[{"entity_type": "invoice_number", "value": "INV-001"}])
        result = MissingInvoiceNumberRule().evaluate(ctx)
        assert result.triggered is False

    def test_empty_document_detected(self):
        ctx = make_ctx(raw_text="   ")
        result = EmptyDocumentRule().evaluate(ctx)
        assert result.triggered is True

    def test_nonempty_document_passes(self):
        ctx = make_ctx(raw_text="This document has real content in it.")
        result = EmptyDocumentRule().evaluate(ctx)
        assert result.triggered is False


class TestRiskScoring:
    def test_no_findings_gives_zero_risk(self):
        assert calculate_risk_score([]) == 0.0

    def test_critical_finding_dominates_score(self):
        findings = [{"triggered": True, "severity": "critical", "confidence": 1.0}]
        score = calculate_risk_score(findings)
        assert score >= 60

    def test_score_to_level_boundaries(self):
        thresholds = {"medium": 25, "high": 60, "critical": 85}
        assert score_to_level(10, thresholds) == "low"
        assert score_to_level(30, thresholds) == "medium"
        assert score_to_level(70, thresholds) == "high"
        assert score_to_level(90, thresholds) == "critical"

    def test_route_mapping_covers_all_levels(self):
        assert route_for_level("low") == "auto_approve"
        assert route_for_level("medium") == "reviewer_queue"
        assert route_for_level("high") == "senior_auditor"
        assert route_for_level("critical") == "immediate_escalation"

    def test_score_never_exceeds_100(self):
        findings = [{"triggered": True, "severity": "critical", "confidence": 1.0}] * 10
        assert calculate_risk_score(findings) == 100.0


@pytest_asyncio.fixture
async def processed_invoice_for_rules(client, user_headers, sample_invoice_bytes):
    files = {"files": (f"rule-fixture-invoice-{uuid.uuid4().hex[:8]}.txt", sample_invoice_bytes, "text/plain")}
    upload = await client.post("/api/v1/documents/upload", headers=user_headers, files=files)
    doc_id = upload.json()["results"][0]["document_id"]
    await client.post(f"/api/v1/classification/{doc_id}/classify", headers=user_headers)
    await client.post(f"/api/v1/parsing/{doc_id}/parse", headers=user_headers)
    await client.post(f"/api/v1/canonical/{doc_id}/build", headers=user_headers)
    await client.post(f"/api/v1/extraction/{doc_id}/extract", headers=user_headers)
    return doc_id


class TestRuleEngineAPI:
    @pytest_asyncio.fixture
    async def seeded_rules(self, client, admin_headers):
        resp = await client.post("/api/v1/rules/seed", headers=admin_headers)
        assert resp.status_code == 200
        return True

    async def test_list_rules_returns_seeded_catalog(self, client, admin_headers, seeded_rules):
        resp = await client.get("/api/v1/rules", headers=admin_headers)
        assert resp.status_code == 200
        keys = {r["rule_key"] for r in resp.json()}
        assert "missing_invoice_number" in keys

    async def test_execute_rules_on_bad_invoice_flags_findings(self, client, user_headers, admin_headers, seeded_rules, sample_invoice_text):
        bad_text = sample_invoice_text.replace("Total: 165.00", "Total: 5000.00")
        files = {"files": (f"rule-test-invoice-{uuid.uuid4().hex[:8]}.txt", bad_text.encode(), "text/plain")}
        upload = await client.post("/api/v1/documents/upload", headers=user_headers, files=files)
        doc_id = upload.json()["results"][0]["document_id"]
        await client.post(f"/api/v1/classification/{doc_id}/classify", headers=user_headers)
        await client.post(f"/api/v1/parsing/{doc_id}/parse", headers=user_headers)
        await client.post(f"/api/v1/canonical/{doc_id}/build", headers=user_headers)
        await client.post(f"/api/v1/extraction/{doc_id}/extract", headers=user_headers)

        resp = await client.post(f"/api/v1/rules/{doc_id}/execute", headers=user_headers)
        assert resp.status_code == 200
        run = resp.json()
        assert run["rules_triggered"] >= 1
        assert run["risk_level"] in ("low", "medium", "high", "critical")

        findings = (await client.get(f"/api/v1/rules/{doc_id}/findings", headers=user_headers)).json()
        triggered_keys = {f["rule_key"] for f in findings if f["triggered"]}
        assert "total_equals_subtotal_plus_tax" in triggered_keys

    async def test_disable_rule_excludes_it_from_execution(self, client, user_headers, admin_headers, seeded_rules, processed_invoice_for_rules):
        await client.post("/api/v1/rules/missing_due_date/disable", headers=admin_headers)
        resp = await client.post(f"/api/v1/rules/{processed_invoice_for_rules}/execute", headers=user_headers)
        findings = (await client.get(f"/api/v1/rules/{processed_invoice_for_rules}/findings", headers=user_headers)).json()
        assert "missing_due_date" not in {f["rule_key"] for f in findings}

    async def test_unauthorized_user_cannot_manage_rules(self, client, user_headers):
        resp = await client.post("/api/v1/rules/some_rule/disable", headers=user_headers)
        assert resp.status_code == 403


class TestPostLLMResponseValidation:
    def test_flags_contradicting_number(self):
        from app.rule_engine.response_validator import validate_llm_response_against_facts
        response = "The invoice total is 500.00."
        facts = {"invoice_total": 165.0}
        contradictions = validate_llm_response_against_facts(response, facts)
        assert len(contradictions) == 1
        assert contradictions[0]["fact_type"] == "invoice_total"

    def test_no_contradiction_when_numbers_match(self):
        from app.rule_engine.response_validator import validate_llm_response_against_facts
        response = "The invoice total is 165.00."
        facts = {"invoice_total": 165.0}
        contradictions = validate_llm_response_against_facts(response, facts)
        assert contradictions == []