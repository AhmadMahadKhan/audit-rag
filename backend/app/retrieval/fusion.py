# ===== app/retrieval/fusion.py =====
"""Reciprocal Rank Fusion — score-scale-agnostic, standard choice for
combining dense (cosine) and sparse (BM25) result sets."""

def reciprocal_rank_fusion(result_lists: list[list[str]], k: int = 60) -> dict[str, float]:
    """result_lists: list of ranked chunk_id lists (best first). Returns {chunk_id: fused_score}."""
    scores: dict[str, float] = {}
    for results in result_lists:
        for rank, chunk_id in enumerate(results):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank + 1)
    return scores

def weighted_fusion(dense: dict[str, float], sparse: dict[str, float], dense_weight: float = 0.6) -> dict[str, float]:
    """Alternative to RRF — needs score normalization first since dense (cosine ~0-1)
    and BM25 (unbounded) aren't on the same scale."""
    def normalize(d: dict[str, float]) -> dict[str, float]:
        if not d:
            return {}
        max_v = max(d.values()) or 1.0
        return {k: v / max_v for k, v in d.items()}

    dense_n, sparse_n = normalize(dense), normalize(sparse)
    all_ids = set(dense_n) | set(sparse_n)
    return {cid: dense_weight * dense_n.get(cid, 0) + (1 - dense_weight) * sparse_n.get(cid, 0) for cid in all_ids}
