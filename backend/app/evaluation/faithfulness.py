
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

async def score_faithfulness(answer: str, context: str, model: str = "llama3.1") -> dict:
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(f"{settings.OLLAMA_URL}/api/generate", json={
                "model": model, "prompt": JUDGE_PROMPT.format(context=context[:3000], answer=answer),
                "stream": False, "format": "json",
            })
            resp.raise_for_status()
            result = json.loads(resp.json().get("response", "{}"))
            return {"faithfulness_score": float(result.get("faithfulness_score", 0.0)),
                    "unsupported_claims": result.get("unsupported_claims", [])}
    except Exception as e:
        logger.error("faithfulness_judge_failed", error=str(e))
        return {"faithfulness_score": None, "unsupported_claims": [], "error": str(e)}
