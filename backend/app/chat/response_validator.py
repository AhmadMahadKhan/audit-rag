
# ===== app/chat/response_validator.py =====
"""Post-generation checks per the hallucination-prevention spec. Does not
call the Rule Engine (that's a separate phase) — this validates the LLM's
OWN output shape/grounding, not business facts."""

def validate_response(response_text: str, citations: list[dict], context_chunks: list[dict]) -> tuple[str, float]:
    """Returns (status, confidence)."""
    if not response_text.strip():
        return "refused", 0.0

    refusal_phrases = ["i don't have enough information", "cannot find", "no relevant information"]
    if any(p in response_text.lower() for p in refusal_phrases):
        return "refused", 0.0

    if not context_chunks:
        return "low_confidence", 0.2

    citation_coverage = len(citations) / max(len(response_text.split(". ")), 1)
    avg_context_score = sum(c.get("final_score", c.get("fused_score", 0.5)) for c in context_chunks) / len(context_chunks)
    confidence = min(1.0, 0.5 * avg_context_score + 0.5 * min(citation_coverage * 3, 1.0))

    if not citations:
        return "low_confidence", min(confidence, 0.35)

    return "valid", confidence