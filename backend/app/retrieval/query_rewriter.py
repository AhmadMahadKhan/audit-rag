# ===== app/retrieval/query_rewriter.py =====
"""LLM-based query rewriting via Ollama — reduces a conversational question
to search-optimized keywords. Falls back to the cleaned original on failure."""
import httpx
from app.core.config import settings
from app.core.logging_config import logger

PROMPT = """Rewrite this question as a short keyword search query for document
retrieval. Keep named entities and numbers exact. Return ONLY the rewritten
query, nothing else.

Question: {query}"""

async def rewrite_query(query: str, model: str = "llama3.1") -> str:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(f"{settings.OLLAMA_URL}/api/generate",
                json={"model": model, "prompt": PROMPT.format(query=query), "stream": False})
            resp.raise_for_status()
            rewritten = resp.json().get("response", "").strip()
            return rewritten if rewritten else query
    except Exception as e:
        logger.warning("query_rewrite_failed", error=str(e))
        return query