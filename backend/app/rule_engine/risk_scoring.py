
# ===== app/rule_engine/risk_scoring.py =====
"""Configurable severity weights + thresholds — pure function, easy to unit test."""
SEVERITY_WEIGHTS = {"low": 5, "medium": 15, "high": 35, "critical": 60}

def calculate_risk_score(findings: list[dict]) -> float:
    score = 0.0
    for f in findings:
        if f["triggered"]:
            score += SEVERITY_WEIGHTS.get(f["severity"], 10) * f.get("confidence", 1.0)
    return min(score, 100.0)

def score_to_level(score: float, thresholds: dict) -> str:
    if score >= thresholds["critical"]:
        return "critical"
    if score >= thresholds["high"]:
        return "high"
    if score >= thresholds["medium"]:
        return "medium"
    return "low"

def route_for_level(level: str) -> str:
    return {"low": "auto_approve", "medium": "reviewer_queue",
            "high": "senior_auditor", "critical": "immediate_escalation"}[level]
