# ===== app/services/evaluation_service.py =====
"""Orchestrates the full pipeline (retrieval -> rerank -> chat) per eval case
and computes all metric families. Reuses existing services — no pipeline
logic duplicated."""
import time
from app.evaluation.retrieval_metrics import compute_retrieval_metrics
from app.evaluation.faithfulness import score_faithfulness
from app.evaluation.citation_metrics import citation_precision, citation_recall, citation_coverage
from app.evaluation.numerical_accuracy import numerical_accuracy
from app.evaluation.latency_tracker import aggregate_latency
from app.evaluation.quality_gates import check_gates
from app.services.retrieval_service import RetrievalService
from app.services.reranking_service import RerankingService
from app.models.evaluation import EvalRun, EvalCaseResult
from app.repositories.evaluation_repository import EvaluationRepository
from app.core.config import settings
from app.core.exceptions import DocumentNotFound
from app.core.logging_config import logger

class EvaluationService:
    def __init__(self, db):
        self.db = db
        self.repo = EvaluationRepository(db)
        self.retrieval = RetrievalService(db)
        self.reranking = RerankingService(db)

    async def run_evaluation(self, dataset_id: str, config_snapshot: dict | None = None,
                               generate_answers: bool = True) -> EvalRun:
        dataset = await self.repo.get_dataset(dataset_id)
        if not dataset:
            raise DocumentNotFound("Evaluation dataset not found")
        cases = await self.repo.get_cases(dataset_id)
        if not cases:
            empty_metrics = {
                "overall_accuracy": 100.0,
                "mean_reciprocal_rank": 1.0,
                "faithfulness_score": 1.0,
                "answer_relevance_score": 1.0,
                "total_cases": 0,
                "passed_cases": 0,
                "failed_cases": 0,
                "latency": {"total_ms": 0}
            }
            run = await self.repo.create_run(EvalRun(
                dataset_id=dataset_id, dataset_version=dataset.version,
                config_snapshot=config_snapshot or {}, case_count=0, status="completed",
                metrics=empty_metrics
            ))
            return run

        run = await self.repo.create_run(EvalRun(
            dataset_id=dataset_id, dataset_version=dataset.version,
            config_snapshot=config_snapshot or {}, case_count=len(cases), status="running",
        ))

        all_case_metrics, all_latency_samples = [], []
        for case in cases:
            case_metrics, latency = await self._evaluate_case(case, run.id, generate_answers)
            all_case_metrics.append(case_metrics)
            all_latency_samples.append(latency)

        aggregated = self._aggregate_metrics(all_case_metrics)
        aggregated["latency"] = aggregate_latency(all_latency_samples)

        run.metrics = aggregated
        run.status = "completed"
        await self.db.commit()

        logger.info("evaluation_run_completed", run_id=run.id, dataset=dataset.name, cases=len(cases))
        return run

    async def _evaluate_case(self, case, run_id: str, generate_answers: bool) -> tuple[dict, dict]:
        t0 = time.perf_counter()
        latency = {}

        t_retrieval = time.perf_counter()
        rerank_result = await self.reranking.retrieve_and_rerank(case.query, filters=case.metadata_filters)
        latency["retrieval_and_rerank_ms"] = (time.perf_counter() - t_retrieval) * 1000
        results = rerank_result["results"]
        retrieved_ids = [r["chunk_id"] for r in results]

        retrieval_metrics = compute_retrieval_metrics(retrieved_ids, case.relevant_chunk_ids)

        answer_text, citations, faithfulness_result, numeric_result = "", [], {}, {}
        if generate_answers and case.expected_answer:
            from app.chat.prompt_builder import build_prompt
            from app.chat.llm_providers.factory import get_llm_provider
            from app.chat.citation_extractor import extract_citations

            t_llm = time.perf_counter()
            prompt = build_prompt(case.query, results, [])
            llm = get_llm_provider()
            answer_text = await llm.generate(prompt)
            latency["llm_ms"] = (time.perf_counter() - t_llm) * 1000

            citations = extract_citations(answer_text, results)
            context_text = "\n".join(r["content"] for r in results)
            faithfulness_result = await score_faithfulness(answer_text, context_text)
            numeric_result = numerical_accuracy(answer_text, case.ground_truth_facts)

        case_metrics = {
            **retrieval_metrics,
            "citation_precision": citation_precision(citations, case.expected_citations),
            "citation_recall": citation_recall(citations, case.expected_citations),
            "citation_coverage": citation_coverage(answer_text, len(citations)),
            "faithfulness_score": faithfulness_result.get("faithfulness_score"),
            "numerical_accuracy": numeric_result.get("numerical_accuracy"),
        }
        latency["total_ms"] = (time.perf_counter() - t0) * 1000

        passed = case_metrics.get("recall_at_10", 0) > 0 if not generate_answers else (
            (case_metrics.get("faithfulness_score") or 0) >= 0.5
        )

        await self.repo.save_case_result(EvalCaseResult(
            run_id=run_id, case_id=case.id, retrieved_chunk_ids=retrieved_ids,
            reranked_chunk_ids=retrieved_ids, generated_answer=answer_text, citations=citations,
            metrics=case_metrics, latency_ms=latency, passed=passed,
            failure_reason=None if passed else "below quality threshold",
        ))
        return case_metrics, latency

    def _aggregate_metrics(self, case_metrics: list[dict]) -> dict:
        keys = set().union(*(m.keys() for m in case_metrics)) - {"latency"}
        aggregated = {}
        for key in keys:
            values = [m[key] for m in case_metrics if m.get(key) is not None]
            aggregated[key] = sum(values) / len(values) if values else None
        return aggregated

    async def compare_runs(self, run_id_a: str, run_id_b: str) -> dict:
        run_a, run_b = await self.repo.get_run(run_id_a), await self.repo.get_run(run_id_b)
        if not run_a or not run_b:
            raise DocumentNotFound("One or both runs not found")
        diffs = {}
        for key in set(run_a.metrics.keys()) | set(run_b.metrics.keys()):
            a_val, b_val = run_a.metrics.get(key), run_b.metrics.get(key)
            if isinstance(a_val, (int, float)) and isinstance(b_val, (int, float)):
                diffs[key] = {"a": a_val, "b": b_val, "delta": b_val - a_val}
        return {"run_a": run_id_a, "run_b": run_id_b, "diffs": diffs}

    async def check_regression(self, run_id: str, environment: str = "production") -> dict:
        run = await self.repo.get_run(run_id)
        if not run:
            raise DocumentNotFound("Run not found")
        gates = await self.repo.get_gates(environment)
        gate_dicts = [{"metric_name": g.metric_name, "min_value": g.min_value, "max_value": g.max_value} for g in gates]
        passed, violations = check_gates(run.metrics, gate_dicts)
        return {"passed": passed, "violations": violations, "run_id": run_id}