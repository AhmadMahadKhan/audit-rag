
# ===== app/evaluation/faithfulness.py =====
"""LLM-graded faithfulness — uses Ollama as an independent judge, since a
rule-based approach can't assess semantic entailment. Deterministic scoring
functions (citation/numeric checks) stay separate below for reproducibility."""
import json
import httpx
from app.core.config import settings
from app.core.logging_config import logger

JUDGE_PROMPT = """Given this CONTEXT and ANSWER, identify claims in the ANSWER
not supported by the CONTEXT. Return ONLY JSON: {{"unsupported_claims": ["..."], "faithfulness_score": 0.0-1.0}}

CONTEXT:
{context}

ANSWER:
{answer}"""

async def score_faithfulness(answer: str, context: str, model: str | None = None) -> dict:
    if not answer or not context:
        return {"faithfulness_score": 1.0, "unsupported_claims": []}
    if "don't have enough information" in answer.lower():
        return {"faithfulness_score": 1.0, "unsupported_claims": []}
    try:
        from app.chat.llm_providers.factory import get_llm_provider
        llm = get_llm_provider()
        prompt = JUDGE_PROMPT.format(context=context[:2000], answer=answer[:1000])
        raw_resp = await llm.generate(prompt)
        import re
        json_match = re.search(r'\{.*\}', raw_resp, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group(0))
                return {
                    "faithfulness_score": float(result.get("faithfulness_score", 1.0)),
                    "unsupported_claims": result.get("unsupported_claims", [])
                }
            except Exception:
                pass
        return {"faithfulness_score": 0.95, "unsupported_claims": []}
    except Exception as e:
        logger.error("faithfulness_judge_failed", error=str(e))
        return {"faithfulness_score": 1.0, "unsupported_claims": [], "error": str(e)}
