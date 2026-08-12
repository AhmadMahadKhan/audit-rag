
# ===== app/observability/redaction.py =====
"""Field-level redaction applied to every structured log line — the concrete
implementation of Phase 20's 'Security & Privacy' requirements."""
import re

SENSITIVE_KEYS = {"password", "hashed_password", "token", "access_token", "refresh_token",
                   "api_key", "secret", "authorization", "ssn", "credit_card"}

def redact_dict(data: dict) -> dict:
    redacted = {}
    for k, v in data.items():
        if any(s in k.lower() for s in SENSITIVE_KEYS):
            redacted[k] = "***REDACTED***"
        elif isinstance(v, dict):
            redacted[k] = redact_dict(v)
        elif isinstance(v, str) and len(v) > 2000:
            redacted[k] = v[:200] + "...[truncated, full document content not logged]"
        else:
            redacted[k] = v
    return redacted

def redact_text(text: str) -> str:
    text = re.sub(r"Bearer\s+[\w\-.]+", "Bearer ***REDACTED***", text)
    text = re.sub(r"\b\d{3}-\d{2}-\d{4}\b", "***SSN-REDACTED***", text)
    return text