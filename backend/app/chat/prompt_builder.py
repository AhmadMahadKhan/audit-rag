# ===== app/chat/prompt_builder.py =====
"""Versioned prompt template — grounds the LLM strictly in retrieved context
and enforces citation + refusal behavior per the hallucination-prevention spec."""

SYSTEM_PROMPT_V1 = """You are an enterprise document intelligence and audit assistant.

Rules & Priority:
1. FIRST & TOP PRIORITY — Check the RAG Data: Always inspect the provided Context (retrieved RAG document data) first. Treat the document facts, statements, numbers, and findings as your primary source of truth.
2. Verify & Validate Results: Analyze the retrieved RAG data against the question or prompt to verify whether it validly answers, confirms, or refutes the request. If context contains partial or related data, verify its validity and summarize the findings clearly.
3. Traceable Inline Citations: Cite source evidence inline using [Doc: <document_id>, Page: <page>] for all factual claims derived from the context.
4. Objective Response: Be concise, clear, and direct. If the retrieved RAG data lacks relevant information to verify or answer the question, state what data was found in the document and explain what specific information is missing.
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