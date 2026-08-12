# ===== app/evaluation/retrieval_metrics.py =====
"""Pure, deterministic metric functions — required for reproducibility per spec."""

def recall_at_k(retrieved: list[str], relevant: list[str], k: int) -> float:
    if not relevant:
        return 0.0
    top_k = set(retrieved[:k])
    return len(top_k & set(relevant)) / len(relevant)

def precision_at_k(retrieved: list[str], relevant: list[str], k: int) -> float:
    top_k = retrieved[:k]
    if not top_k:
        return 0.0
    return len(set(top_k) & set(relevant)) / len(top_k)

def mrr(retrieved: list[str], relevant: list[str]) -> float:
    for i, r in enumerate(retrieved, start=1):
        if r in relevant:
            return 1.0 / i
    return 0.0

def ndcg_at_k(retrieved: list[str], relevant: list[str], k: int) -> float:
    import math
    top_k = retrieved[:k]
    dcg = sum(1.0 / math.log2(i + 2) for i, r in enumerate(top_k) if r in relevant)
    ideal_hits = min(len(relevant), k)
    idcg = sum(1.0 / math.log2(i + 2) for i in range(ideal_hits))
    return dcg / idcg if idcg > 0 else 0.0

def hit_rate(retrieved: list[str], relevant: list[str], k: int) -> float:
    return 1.0 if set(retrieved[:k]) & set(relevant) else 0.0

def compute_retrieval_metrics(retrieved: list[str], relevant: list[str], k_values=(1, 5, 10, 20, 50)) -> dict:
    metrics = {"mrr": mrr(retrieved, relevant)}
    for k in k_values:
        metrics[f"recall_at_{k}"] = recall_at_k(retrieved, relevant, k)
        metrics[f"precision_at_{k}"] = precision_at_k(retrieved, relevant, k)
        metrics[f"ndcg_at_{k}"] = ndcg_at_k(retrieved, relevant, k)
    return metrics