# ===== app/chat/prompt_builder.py =====
"""Versioned prompt template — grounds the LLM strictly in retrieved context
and enforces citation + refusal behavior per the hallucination-prevention spec."""

SYSTEM_PROMPT_V1 = """You are an enterprise document assistant. Answer ONLY using the provided context.

Rules:
- Every factual claim must be traceable to the context below.
- If the context does not contain the answer, say "I don't have enough information in the documents to answer this."
- Cite sources inline using [Doc: <document_id>, Page: <page>] after each claim.
- Do not speculate or use outside knowledge.
- Be concise and direct.
"""

PROMPT_VERSION = "1.0"

def build_prompt(question: str, context_chunks: list[dict], history: list[dict]) -> str:
    context_block = "\n\n".join(
        f"[Source {i+1} | Doc: {c['document_id']} | Page: {c.get('pages', ['?'])[0]}]\n{c['content']}"
        for i, c in enumerate(context_chunks)
    )
    history_block = "\n".join(f"{m['role']}: {m['content']}" for m in history[-6:])  # last 3 turns

    return f"""{SYSTEM_PROMPT_V1}

Conversation so far:
{history_block if history_block else '(none)'}

Context:
{context_block if context_block else '(no relevant context found)'}

Question: {question}

Answer:"""