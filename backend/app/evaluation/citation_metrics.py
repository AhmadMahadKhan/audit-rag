
# ===== app/evaluation/citation_metrics.py =====

def citation_precision(generated_citations: list[dict], expected_citations: list[dict]) -> float:
    if not generated_citations:
        return 0.0
    expected_keys = {(c.get("document_id"), str(c.get("page"))) for c in expected_citations}
    correct = sum(1 for c in generated_citations if (c.get("document_id"), str(c.get("page"))) in expected_keys)
    return correct / len(generated_citations)

def citation_recall(generated_citations: list[dict], expected_citations: list[dict]) -> float:
    if not expected_citations:
        return 1.0
    generated_keys = {(c.get("document_id"), str(c.get("page"))) for c in generated_citations}
    expected_keys = {(c.get("document_id"), str(c.get("page"))) for c in expected_citations}
    correct = len(generated_keys & expected_keys)
    return correct / len(expected_keys)

def citation_coverage(answer: str, citation_count: int) -> float:
    """Fraction of sentences that carry a citation marker — proxy for coverage."""
    sentence_count = max(len([s for s in answer.split(".") if s.strip()]), 1)
    return min(citation_count / sentence_count, 1.0)
