
# ===== app/chat/citation_extractor.py =====
import re

CITATION_PATTERN = re.compile(r"\[Doc:\s*([^\],]+),\s*Page:\s*([^\]]+)\]")

def extract_citations(response_text: str, context_chunks: list[dict]) -> list[dict]:
    """Parses [Doc: X, Page: Y] markers the LLM was instructed to emit and
    resolves them back to full chunk metadata for the frontend citation panel."""
    found = CITATION_PATTERN.findall(response_text)
    citations = []
    seen = set()
    for doc_id, page in found:
        key = (doc_id.strip(), page.strip())
        if key in seen:
            continue
        seen.add(key)
        matching = next((c for c in context_chunks if c["document_id"] == doc_id.strip()), None)
        citations.append({
            "document_id": doc_id.strip(), "page": page.strip(),
            "chunk_id": matching["chunk_id"] if matching else None,
            "section_name": matching.get("section_name") if matching else None,
        })
    return citations