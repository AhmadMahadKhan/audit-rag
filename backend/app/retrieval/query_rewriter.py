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

async def rewrite_query(query: str, model: str | None = None) -> str:
    try:
        from app.chat.llm_providers.factory import get_llm_provider
        llm = get_llm_provider()
        prompt = PROMPT.format(query=query)
        rewritten = await llm.generate(prompt)
        cleaned = rewritten.strip() if rewritten else query
        return cleaned if cleaned else query
    except Exception as e:
        logger.warning("query_rewrite_failed", error=str(e))
        return query