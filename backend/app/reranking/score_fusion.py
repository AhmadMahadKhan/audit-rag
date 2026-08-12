# ===== app/reranking/score_fusion.py =====
"""Combines retrieval score(s) with the cross-encoder score into one final
relevance number. Cross-encoder score dominates since it's query-aware and
directly optimized for relevance; retrieval score is a lightweight tiebreaker."""

def fuse_scores(fused_retrieval_score: float, rerank_score: float, rerank_weight: float = 0.8) -> float:
    # rerank_score from CrossEncoder can be any real number (not bounded) —
    # sigmoid-normalize before fusing so it's comparable to the 0-1 retrieval score
    import math
    normalized_rerank = 1 / (1 + math.exp(-rerank_score))
    return rerank_weight * normalized_rerank + (1 - rerank_weight) * min(fused_retrieval_score, 1.0)