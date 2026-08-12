
# ===== app/embeddings/content_builders.py =====
"""Builds the text string to embed for each embedding type, given related DB rows."""

def build_metadata_text(fields: list[dict]) -> str:
    
    return "; ".join(f"{f['key']}: {f['value']}" for f in fields if f.get("value"))

def build_entity_text(entity_type: str, value: str) -> str:
    return f"{entity_type}: {value}"

def build_table_text(table_content: str) -> str:
    return table_content

def build_summary_text(raw_text: str, max_chars: int = 1500) -> str:
    """Naive truncation-based 'summary' — a real summarizer (Ollama LLM call)
    is the correct long-term approach; flagged as a placeholder here since
    Phase 15 (Chat Engine) introduces the LLM chain properly."""
    return raw_text[:max_chars]
