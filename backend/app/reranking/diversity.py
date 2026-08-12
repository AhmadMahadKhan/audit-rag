# ===== app/reranking/diversity.py =====
"""Removes near-duplicate chunks post-rerank. Uses simple token-overlap
(Jaccard) rather than a second embedding pass — cheap, no extra model call,
adequate for catching copy-pasted boilerplate across chunks."""

def jaccard_similarity(a: str, b: str) -> float:
    set_a, set_b = set(a.lower().split()), set(b.lower().split())
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)

def deduplicate_diverse(items: list[dict], threshold: float = 0.85, content_key: str = "content") -> list[dict]:
    kept = []
    for item in items:
        is_dup = any(jaccard_similarity(item[content_key], k[content_key]) > threshold for k in kept)
        if not is_dup:
            kept.append(item)
    return kept

def enforce_document_diversity(items: list[dict], max_per_document: int = 3) -> list[dict]:
    """Caps how many chunks from a single document dominate the final context."""
    counts: dict[str, int] = {}
    result = []
    for item in items:
        doc_id = item["document_id"]
        if counts.get(doc_id, 0) < max_per_document:
            result.append(item)
            counts[doc_id] = counts.get(doc_id, 0) + 1
    return result