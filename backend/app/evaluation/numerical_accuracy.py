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

def numerical_accuracy(answer: str, ground_truth_facts: dict | list | None, tolerance: float = 0.02) -> dict:
    answer_numbers = extract_numbers(answer or "")
    matched, total = 0, 0
    mismatches = []

    if not ground_truth_facts:
        return {"numerical_accuracy": None, "mismatches": []}

    if isinstance(ground_truth_facts, dict):
        items = list(ground_truth_facts.items())
    elif isinstance(ground_truth_facts, list):
        items = [(f"fact_{i}", item) for i, item in enumerate(ground_truth_facts)]
    else:
        items = [("fact_0", ground_truth_facts)]

    for fact_type, raw_expected in items:
        if raw_expected is None:
            continue

        exp_nums = []
        if isinstance(raw_expected, (int, float)):
            exp_nums = [float(raw_expected)]
        elif isinstance(raw_expected, str):
            exp_nums = extract_numbers(raw_expected)

        if not exp_nums:
            continue

        total += 1
        expected = exp_nums[0]
        if any(abs(n - expected) <= tolerance * max(abs(expected), 1.0) for n in answer_numbers):
            matched += 1
        else:
            mismatches.append({"fact_type": fact_type, "expected": raw_expected})

    accuracy = (matched / total) if total > 0 else None
    return {"numerical_accuracy": accuracy, "mismatches": mismatches}
