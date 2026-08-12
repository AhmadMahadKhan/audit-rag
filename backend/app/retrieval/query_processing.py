# ===== app/retrieval/query_processing.py =====
import re
from spellchecker import SpellChecker

_spell = SpellChecker()
STOPWORDS = {"the", "a", "an", "is", "are", "of", "to", "in", "for", "on", "and", "did", "we"}

ACRONYMS = {"po": "purchase order", "inv": "invoice", "vat": "value added tax", "gst": "goods and services tax"}

def normalize_query(query: str) -> str:
    return " ".join(query.strip().split())

def correct_spelling(query: str) -> str:
    words = query.split()
    corrected = []
    for w in words:
        clean = re.sub(r"[^\w]", "", w)
        if clean and clean.lower() not in _spell:
            suggestion = _spell.correction(clean)
            corrected.append(suggestion if suggestion else w)
        else:
            corrected.append(w)
    return " ".join(corrected)

def resolve_acronyms(query: str) -> str:
    words = query.split()
    return " ".join(ACRONYMS.get(w.lower().strip("?."), w) for w in words)

def strip_stopwords_for_bm25(query: str) -> str:
    """BM25 benefits from stopword removal; dense embeddings don't — kept separate."""
    return " ".join(w for w in query.split() if w.lower() not in STOPWORDS)
