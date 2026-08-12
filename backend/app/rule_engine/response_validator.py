# ===== app/rule_engine/response_validator.py =====
"""Phase 15's response_validator checked citation/grounding shape only.
THIS is the deterministic post-LLM layer the spec calls for: cross-checking
LLM-stated numbers against the Fact Store."""
import re

def validate_llm_response_against_facts(response_text: str, facts: dict[str, float], tolerance: float = 0.02) -> list[dict]:
    """Finds numbers in the LLM response and flags any that contradict known facts."""
    contradictions = []
    numbers_in_response = [float(n.replace(",", "")) for n in re.findall(r"\b\d[\d,]*\.?\d*\b", response_text) if n.replace(",", "").replace(".", "").isdigit()]

    for fact_type, fact_value in facts.items():
        if fact_value is None:
            continue
        close_match = any(abs(n - fact_value) <= tolerance * max(fact_value, 1) for n in numbers_in_response)
        mentioned = fact_type.replace("_", " ") in response_text.lower()
        if mentioned and not close_match and numbers_in_response:
            contradictions.append({"fact_type": fact_type, "expected": fact_value, "found_numbers": numbers_in_response})
    return contradictions