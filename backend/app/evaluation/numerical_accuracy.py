# ===== app/evaluation/numerical_accuracy.py =====
import re

def extract_numbers(text: str) -> list[float]:
    matches = re.findall(r"\b\d[\d,]*\.?\d*\b", text)
    out = []
    for m in matches:
        try:
            out.append(float(m.replace(",", "")))
        except ValueError:
            pass
    return out

def numerical_accuracy(answer: str, ground_truth_facts: dict[str, float], tolerance: float = 0.02) -> dict:
    answer_numbers = extract_numbers(answer)
    matched, total = 0, 0
    mismatches = []
    for fact_type, expected in ground_truth_facts.items():
        if expected is None:
            continue
        total += 1
        if any(abs(n - expected) <= tolerance * max(expected, 1) for n in answer_numbers):
            matched += 1
        else:
            mismatches.append({"fact_type": fact_type, "expected": expected})
    accuracy = matched / total if total else None
    return {"numerical_accuracy": accuracy, "mismatches": mismatches}
