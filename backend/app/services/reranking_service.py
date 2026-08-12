# ===== app/services/reranking_service.py =====
import time
from app.reranking.factory import get_reranker
from app.reranking.diversity import deduplicate_diverse, enforce_document_diversity
from app.reranking.score_fusion import fuse_scores
from app.services.retrieval_service import RetrievalService
from app.core.config import settings
from app.core.logging_config import logger

class RerankingService:
    def __init__(self, db):
        self.db = db
        self.retrieval = RetrievalService(db)

    async def retrieve_and_rerank(self, query: str, top_n: int | None = None, filters: dict | None = None,
                                    user_id: str | None = None, provider_name: str | None = None) -> dict:
        t0 = time.perf_counter()
        top_n = top_n or settings.RERANK_TOP_N_OUT

        candidates = await self.retrieval.hybrid_search(
            query, top_k=settings.RERANK_TOP_K_IN, filters=filters, user_id=user_id,
        )
        if not candidates:
            return {"results": [], "fallback_used": False, "latency_ms": 0}

        try:
            reranked = await self._rerank(query, candidates, provider_name)
            fallback_used = False
        except Exception as e:
            logger.error("rerank_failed_falling_back", error=str(e))
            reranked = candidates  # graceful degradation: hybrid order stands
            fallback_used = True

        deduped = deduplicate_diverse(reranked, threshold=1 - (settings.RERANK_DIVERSITY_THRESHOLD - 0.0))
        diverse = enforce_document_diversity(deduped, max_per_document=3)
        final = diverse[:top_n]

        latency_ms = (time.perf_counter() - t0) * 1000
        logger.info("rerank_completed", query=query, candidates=len(candidates), final=len(final),
                     fallback=fallback_used, latency_ms=latency_ms)

        return {"results": final, "fallback_used": fallback_used, "latency_ms": latency_ms,
                "candidates_considered": len(candidates)}

    async def _rerank(self, query: str, candidates: list[dict], provider_name: str | None) -> list[dict]:
        reranker = get_reranker(provider_name)
        texts = [c["content"] for c in candidates]
        rerank_scores = await reranker.score(query, texts)

        for c, score in zip(candidates, rerank_scores):
            c["rerank_score"] = score
            c["final_score"] = fuse_scores(c.get("fused_score", 0.5), score)

        filtered = [c for c in candidates if c["final_score"] >= settings.RERANK_MIN_SCORE]
        return sorted(filtered, key=lambda c: c["final_score"], reverse=True)
