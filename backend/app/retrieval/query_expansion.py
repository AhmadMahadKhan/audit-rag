# ===== app/retrieval/query_expansion.py =====
"""Rule-based synonym expansion. Kept deterministic/transparent per spec
rather than another LLM call — cheaper and auditable for business terms."""
SYNONYMS = {
    "pay": ["payment", "paid"], "cost": ["price", "amount", "total"],
    "vendor": ["supplier", "seller"], "customer": ["client", "buyer"],
    "contract": ["agreement"], "invoice": ["bill"],
}

def expand_query(query: str) -> list[str]:
    """Returns [original, ...expanded_variants] — caller decides how to use them."""
    variants = {query}
    words = query.lower().split()
    for word in words:
        clean = word.strip("?.,")
        if clean in SYNONYMS:
            for syn in SYNONYMS[clean]:
                variants.add(query.lower().replace(clean, syn))
    return list(variants)
