
# ===== app/evaluation/quality_gates.py =====

def check_gates(metrics: dict, gates: list[dict]) -> tuple[bool, list[dict]]:
    """gates: [{metric_name, min_value, max_value}]. Returns (passed, violations)."""
    violations = []
    for gate in gates:
        value = metrics.get(gate["metric_name"])
        if value is None:
            continue
        if gate.get("min_value") is not None and value < gate["min_value"]:
            violations.append({"metric": gate["metric_name"], "value": value, "required_min": gate["min_value"]})
        if gate.get("max_value") is not None and value > gate["max_value"]:
            violations.append({"metric": gate["metric_name"], "value": value, "required_max": gate["max_value"]})
    return len(violations) == 0, violations