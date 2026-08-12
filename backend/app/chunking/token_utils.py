
# ===== app/chunking/token_utils.py =====
def estimate_tokens(text: str) -> int:
    
    return max(1, len(text) // 4)
