# ===== app/search_ui/formatter.py =====
"""Formats raw retrieval/rerank output into the explainable result shape
the search UI needs (preview snippet, highlighted match, why-it-matched)."""
import re

def make_snippet(content: str, query: str, window: int = 160) -> str:
    idx = content.lower().find(query.lower().split()[0].lower()) if query.split() else -1
    if idx == -1:
        return content[:window] + ("..." if len(content) > window else "")
    start = max(0, idx - window // 2)
    end = min(len(content), idx + window // 2)
    snippet = content[start:end]
    return ("..." if start > 0 else "") + snippet + ("..." if end < len(content) else "")

def highlight_terms(snippet: str, query: str) -> str:
    terms = [re.escape(t) for t in query.split() if len(t) > 2]
    if not terms:
        return snippet
    pattern = re.compile(r"(" + "|".join(terms) + r")", re.IGNORECASE)
    return pattern.sub(r"**\1**", snippet)  # markdown-style bold; frontend renders as highlight

def format_result(item: dict, query: str, document_title: str) -> dict:
    snippet = make_snippet(item["content"], query)
    return {
        "document_id": item["document_id"], "document_title": document_title,
        "chunk_id": item["chunk_id"], "snippet": highlight_terms(snippet, query),
        "page": item["pages"][0] if item.get("pages") else None,
        "section_name": item.get("section_name"),
        "hybrid_score": item.get("fused_score"), "rerank_score": item.get("rerank_score"),
        "final_score": item.get("final_score", item.get("fused_score")),
        "retrieval_method": item.get("retrieval_method", "hybrid"),
    }