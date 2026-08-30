# ===== app/audit_agent/memory.py =====
"""Safe merge/defaults/size-capping for the running memory JSON — this is
what keeps a long multi-document audit from growing its own memory beyond
what fits in a later prompt."""
import json
from app.chunking.token_utils import estimate_tokens

SEVERITY_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1}

def empty_memory() -> dict:
    return {"key_findings": [], "risk_flags": [], "open_questions": [], "documents_processed": []}

def normalize_memory(raw: dict) -> dict:
    """Fills in any missing keys so a malformed LLM JSON response doesn't crash the run."""
    base = empty_memory()
    for key in base:
        if key in raw and isinstance(raw[key], list):
            base[key] = raw[key]
    return base

def estimate_memory_tokens(memory: dict) -> int:
    return estimate_tokens(json.dumps(memory))

def cap_memory_size(memory: dict, max_findings: int) -> dict:
    """Hard safety net independent of the LLM's own compaction — keeps all
    critical/high risk flags no matter what, trims lowest-priority findings."""
    memory["key_findings"] = memory["key_findings"][-max_findings:]
    risk_flags = sorted(memory["risk_flags"], key=lambda f: SEVERITY_RANK.get(f.get("severity", "low"), 0), reverse=True)
    memory["risk_flags"] = risk_flags[: max_findings * 2]  # risk flags matter more, keep more of them
    memory["open_questions"] = memory["open_questions"][-max_findings:]
    return memory