# ===== app/embeddings/validator.py =====
import math

def validate_vector(vector: list[float], expected_dim: int) -> tuple[str, str | None]:
    if not vector:
        return "invalid", "empty vector"
    if len(vector) != expected_dim:
        return "invalid", f"dimension mismatch: got {len(vector)}, expected {expected_dim}"
    if any(math.isnan(v) or math.isinf(v) for v in vector):
        return "invalid", "vector contains NaN/Inf"
    if all(v == 0 for v in vector):
        return "invalid", "zero vector"
    return "valid", None