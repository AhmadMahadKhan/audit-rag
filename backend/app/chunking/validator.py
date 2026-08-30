
# ===== app/chunking/validator.py =====
from app.chunking.schema import ChunkCandidate
from app.chunking.token_utils import estimate_tokens

MAX_TOKENS = 2000
MIN_CHARS = 10

def validate_chunk(chunk: ChunkCandidate) -> tuple[str, str | None]:
    if not chunk.content.strip():
        return "invalid", "empty chunk"
    if len(chunk.content) < MIN_CHARS:
        return "invalid", "content too short"
    if estimate_tokens(chunk.content) > MAX_TOKENS:
        return "needs_review", "exceeds max token limit"
    return "valid", None

def deduplicate(chunks: list[ChunkCandidate]) -> list[ChunkCandidate]:
    seen, result = set(), []
    for c in chunks:
        key = c.content.strip()
        if key not in seen:
            seen.add(key)
            result.append(c)
    return result
