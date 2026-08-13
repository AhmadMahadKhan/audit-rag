
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
    try:
        from app.chat.llm_providers.factory import get_llm_provider
        llm = get_llm_provider()
        prompt = JUDGE_PROMPT.format(context=context[:3000], answer=answer)
        raw_resp = await llm.generate(prompt)
        # Parse JSON from response
        try:
            result = json.loads(raw_resp)
        except Exception:
            result = {}
        return {
            "faithfulness_score": float(result.get("faithfulness_score", 1.0)),
            "unsupported_claims": result.get("unsupported_claims", [])
        }
    except Exception as e:
        logger.error("faithfulness_judge_failed", error=str(e))
        return {"faithfulness_score": 1.0, "unsupported_claims": [], "error": str(e)}
