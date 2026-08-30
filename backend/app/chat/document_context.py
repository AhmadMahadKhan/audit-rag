from app.chunking.token_utils import estimate_tokens
from app.audit_agent.batching import batch_texts_by_budget
from app.audit_agent.prompts import AUDITOR_SYSTEM_PROMPT, MAP_SUMMARY_PROMPT, COMBINE_SUMMARY_PROMPT
from app.repositories.chunk_repository import ChunkRepository
from app.chat.llm_providers.factory import get_llm_provider

async def load_full_documents_context(db, document_ids: list[str], token_budget: int) -> list[dict]:
    """Loads full content for explicitly selected documents. Fits whole
    when possible; falls back to map-summarize per-document when a
    document's total content exceeds the budget on its own."""
    chunk_repo = ChunkRepository(db)
    context_chunks = []

    for doc_id in document_ids:
        chunks = await chunk_repo.get_for_document(doc_id)
        if not chunks:
            continue

        total_tokens = sum(estimate_tokens(c.content) for c in chunks)

        if total_tokens <= token_budget:
            # Fits whole — pass every chunk through untouched.
            for c in chunks:
                context_chunks.append({
                    "chunk_id": c.id, "document_id": c.document_id, "content": c.content,
                    "pages": c.pages, "section_name": c.section_name,
                    "retrieval_method": "full_document",
                })
        else:
            # Too large — map-summarize this document's chunks, then
            # treat the combined summary as a single context item.
            summary = await _summarize_document(doc_id, chunks, token_budget)
            context_chunks.append({
                "chunk_id": f"{doc_id}_summary", "document_id": doc_id, "content": summary,
                "pages": sorted({p for c in chunks for p in (c.pages or [])}),
                "section_name": "Document Summary (condensed — original exceeded context budget)",
                "retrieval_method": "map_summarized",
            })

    return context_chunks


async def _summarize_document(doc_id: str, chunks, token_budget: int) -> str:
    llm = get_llm_provider()
    texts = [c.content for c in chunks]
    # Leave headroom for prompt scaffolding around each batch.
    batches = batch_texts_by_budget(texts, max_tokens=max(token_budget // 4, 500))

    partial_summaries = []
    for i, batch in enumerate(batches, start=1):
        prompt = MAP_SUMMARY_PROMPT.format(
            system=AUDITOR_SYSTEM_PROMPT, batch_num=i, total_batches=len(batches),
            text="\n\n".join(batch),
        )
        result = await llm.generate(prompt)
        partial_summaries.append(result.strip())

    if len(partial_summaries) == 1:
        return partial_summaries[0]

    combine_prompt = COMBINE_SUMMARY_PROMPT.format(
        system=AUDITOR_SYSTEM_PROMPT, n=len(partial_summaries),
        partial_summaries="\n\n---\n\n".join(partial_summaries),
    )
    combined = await llm.generate(combine_prompt)
    return combined.strip()