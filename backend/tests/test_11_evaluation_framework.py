# ===== tests/test_11_evaluation_framework.py =====
"""Phase 19 — Evaluation metrics (pure function correctness)."""
import pytest


class TestRetrievalMetrics:
    def test_recall_at_k_perfect(self):
        from app.evaluation.retrieval_metrics import recall_at_k
        assert recall_at_k(["a", "b", "c"], ["a", "b"], k=3) == 1.0

    def test_recall_at_k_partial(self):
        from app.evaluation.retrieval_metrics import recall_at_k
        assert recall_at_k(["a", "x", "y"], ["a", "b"], k=3) == 0.5

    def test_recall_at_k_no_relevant_docs_returns_zero(self):
        from app.evaluation.retrieval_metrics import recall_at_k
        assert recall_at_k(["a"], [], k=3) == 0.0

    def test_precision_at_k(self):
        from app.evaluation.retrieval_metrics import precision_at_k
        assert precision_at_k(["a", "b", "x"], ["a", "b"], k=3) == pytest.approx(2 / 3)

    def test_mrr_first_position(self):
        from app.evaluation.retrieval_metrics import mrr
        assert mrr(["a", "b"], ["a"]) == 1.0

    def test_mrr_second_position(self):
        from app.evaluation.retrieval_metrics import mrr
        assert mrr(["x", "a"], ["a"]) == 0.5

    def test_mrr_no_match(self):
        from app.evaluation.retrieval_metrics import mrr
        assert mrr(["x", "y"], ["a"]) == 0.0

    def test_ndcg_perfect_ranking_is_one(self):
        from app.evaluation.retrieval_metrics import ndcg_at_k
        assert ndcg_at_k(["a", "b"], ["a", "b"], k=2) == pytest.approx(1.0)

    def test_ndcg_reversed_ranking_lower_than_perfect(self):
        from app.evaluation.retrieval_metrics import ndcg_at_k
        perfect = ndcg_at_k(["a", "b"], ["a", "b"], k=2)
        reversed_order = ndcg_at_k(["b", "a"], ["a"], k=2)
        assert reversed_order <= perfect

    def test_compute_retrieval_metrics_returns_all_k_values(self):
        from app.evaluation.retrieval_metrics import compute_retrieval_metrics
        metrics = compute_retrieval_metrics(["a", "b"], ["a"], k_values=(1, 5))
        assert "recall_at_1" in metrics and "recall_at_5" in metrics
        assert "mrr" in metrics


class TestCitationMetrics:
    def test_citation_precision_all_correct(self):
        from app.evaluation.citation_metrics import citation_precision
        gen = [{"document_id": "d1", "page": "1"}]
        exp = [{"document_id": "d1", "page": "1"}]
        assert citation_precision(gen, exp) == 1.0

    def test_citation_precision_no_citations(self):
        from app.evaluation.citation_metrics import citation_precision
        assert citation_precision([], [{"document_id": "d1", "page": "1"}]) == 0.0

    def test_citation_recall_missing_expected(self):
        from app.evaluation.citation_metrics import citation_recall
        gen = [{"document_id": "d1", "page": "1"}]
        exp = [{"document_id": "d1", "page": "1"}, {"document_id": "d2", "page": "2"}]
        assert citation_recall(gen, exp) == 0.5

    def test_citation_recall_no_expected_returns_one(self):
        from app.evaluation.citation_metrics import citation_recall
        assert citation_recall([], []) == 1.0


class TestNumericalAccuracy:
    def test_matches_expected_value(self):
        from app.evaluation.numerical_accuracy import numerical_accuracy
        result = numerical_accuracy("The total is 165.00 dollars.", {"invoice_total": 165.0})
        assert result["numerical_accuracy"] == 1.0
        assert result["mismatches"] == []

    def test_flags_mismatch(self):
        from app.evaluation.numerical_accuracy import numerical_accuracy
        result = numerical_accuracy("The total is 500.00 dollars.", {"invoice_total": 165.0})
        assert result["numerical_accuracy"] == 0.0
        assert len(result["mismatches"]) == 1

    def test_no_facts_returns_none_accuracy(self):
        from app.evaluation.numerical_accuracy import numerical_accuracy
        result = numerical_accuracy("some text", {})
        assert result["numerical_accuracy"] is None


class TestLatencyAggregation:
    def test_percentile_calculation(self):
        from app.evaluation.latency_tracker import percentile
        values = list(range(1, 101))  # 1..100
        assert percentile(values, 50) == pytest.approx(51, abs=2)
        assert percentile(values, 99) >= 95

    def test_aggregate_latency_produces_stats_per_stage(self):
        from app.evaluation.latency_tracker import aggregate_latency
        samples = [{"llm_ms": 100}, {"llm_ms": 200}, {"llm_ms": 300}]
        result = aggregate_latency(samples)
        assert result["llm_ms"]["avg"] == 200
        assert "p95" in result["llm_ms"]


class TestQualityGates:
    def test_gate_passes_when_metric_above_min(self):
        from app.evaluation.quality_gates import check_gates
        passed, violations = check_gates({"recall_at_10": 0.8}, [{"metric_name": "recall_at_10", "min_value": 0.5}])
        assert passed is True
        assert violations == []

    def test_gate_fails_when_metric_below_min(self):
        from app.evaluation.quality_gates import check_gates
        passed, violations = check_gates({"recall_at_10": 0.3}, [{"metric_name": "recall_at_10", "min_value": 0.5}])
        assert passed is False
        assert len(violations) == 1

    def test_gate_ignores_missing_metric(self):
        from app.evaluation.quality_gates import check_gates
        passed, violations = check_gates({}, [{"metric_name": "unknown_metric", "min_value": 0.5}])
        assert passed is True


class TestRuleEngineEvaluation:
    def test_perfect_prediction(self):
        from app.evaluation.rule_engine_eval import evaluate_rule_predictions
        result = evaluate_rule_predictions({"rule_a", "rule_b"}, {"rule_a", "rule_b"})
        assert result["precision"] == 1.0
        assert result["recall"] == 1.0
        assert result["f1"] == 1.0

    def test_false_positive_lowers_precision(self):
        from app.evaluation.rule_engine_eval import evaluate_rule_predictions
        result = evaluate_rule_predictions({"rule_a", "rule_x"}, {"rule_a"})
        assert result["false_positives"] == 1
        assert result["precision"] == 0.5

    def test_false_negative_lowers_recall(self):
        from app.evaluation.rule_engine_eval import evaluate_rule_predictions
        result = evaluate_rule_predictions({"rule_a"}, {"rule_a", "rule_b"})
        assert result["false_negatives"] == 1
        assert result["recall"] == 0.5