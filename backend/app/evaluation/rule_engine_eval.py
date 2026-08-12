
# ===== app/evaluation/rule_engine_eval.py =====
"""Evaluates rule accuracy against labeled ground truth (which rules SHOULD
have triggered on a known test document)."""

def evaluate_rule_predictions(predicted_triggered: set[str], expected_triggered: set[str]) -> dict:
    tp = len(predicted_triggered & expected_triggered)
    fp = len(predicted_triggered - expected_triggered)
    fn = len(expected_triggered - predicted_triggered)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {"true_positives": tp, "false_positives": fp, "false_negatives": fn,
            "precision": precision, "recall": recall, "f1": f1}
