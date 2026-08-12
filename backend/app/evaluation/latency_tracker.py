# ===== app/evaluation/latency_tracker.py =====

def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    idx = int(len(sorted_vals) * p / 100)
    idx = min(idx, len(sorted_vals) - 1)
    return sorted_vals[idx]

def aggregate_latency(latency_samples: list[dict]) -> dict:
    """latency_samples: list of per-case {stage: ms}. Returns per-stage avg/p50/p95/p99."""
    stages: dict[str, list[float]] = {}
    for sample in latency_samples:
        for stage, ms in sample.items():
            stages.setdefault(stage, []).append(ms)

    result = {}
    for stage, values in stages.items():
        result[stage] = {
            "avg": sum(values) / len(values), "p50": percentile(values, 50),
            "p95": percentile(values, 95), "p99": percentile(values, 99),
        }
    return result