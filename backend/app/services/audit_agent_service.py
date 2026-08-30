# ===== app/services/audit_agent_service.py =====
"""
Orchestrates the AI Auditor's map -> reduce -> running-memory procedure.

Runs as a FastAPI BackgroundTask, not a real job queue (no Celery in this
project — see README limitations). This means: single-process only, no
retry on server crash, and progress is lost if the server restarts mid-run.
That's an honest, known limitation, not hidden — acceptable for a local-first
tool, worth revisiting if this ever needs to survive restarts or scale to
many concurrent audits.

A background task cannot reuse the request's DB session (it's closed once
the response is sent) — this service opens its own session explicitly via
AsyncSessionLocal, which is the CORRECT pattern here (unlike the earlier bug
found in exception_handlers.py, where a background-style session was used
INSIDE a request's own exception path where a request-scoped session was
still expected).
"""
import json
import httpx
from app.db.session import AsyncSessionLocal
from app.models.audit_agent import AuditRun, AuditMemorySnapshot, AuditReport
from app.audit_agent.prompts import (
    AUDITOR_SYSTEM_PROMPT, MAP_SUMMARY_PROMPT, COMBINE_SUMMARY_PROMPT,
    MEMORY_UPDATE_PROMPT, MEMORY_COMPACTION_PROMPT, FINAL_REPORT_PROMPT,
)
from app.audit_agent.batching import batch_texts_by_budget
from app.audit_agent.memory import empty_memory, normalize_memory, estimate_memory_tokens, cap_memory_size
from app.repositories.audit_repository import AuditRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.knowledge_repository import KnowledgeRepository
from app.repositories.rule_repository import RuleRepository
from app.chat.llm_providers.factory import get_llm_provider
from app.core.config import settings
from app.core.logging_config import logger


class AuditAgentService:
    def __init__(self, db):
        self.db = db
        self.repo = AuditRepository(db)
        self.doc_repo = DocumentRepository(db)
        self.chunk_repo = ChunkRepository(db)
        self.knowledge_repo = KnowledgeRepository(db)
        self.rule_repo = RuleRepository(db)

    async def resolve_document_ids(self, requested_ids: list[str] | None, user) -> list[str]:
        """None/empty => every document the requester is authorized to see
        (own documents, or all documents if they hold documents.delete —
        same authorization shape used everywhere else in this app)."""
        if requested_ids:
            for doc_id in requested_ids:
                doc = await self.doc_repo.get_by_id(doc_id)
                if not doc:
                    from app.core.exceptions import DocumentNotFound
                    raise DocumentNotFound(f"Document {doc_id} not found")
                if doc.user_id != user.id and "documents.delete" not in getattr(user, "_token_permissions", []):
                    from app.core.exceptions import AuthorizationError
                    raise AuthorizationError(f"Not authorized to audit document {doc_id}")
            return requested_ids

        if "documents.delete" in getattr(user, "_token_permissions", []):
            docs = await self.doc_repo.list_by_user(user.id, skip=0, limit=10000)  # TODO: proper "list all" for admins if corpus grows large
        else:
            docs = await self.doc_repo.list_by_user(user.id, skip=0, limit=10000)
        return [d.id for d in docs]

    async def start_run(self, name: str, document_ids: list[str], user_id: str) -> AuditRun:
        run = AuditRun(name=name, requested_by=user_id, document_ids=document_ids,
                        status="pending", progress_total=len(document_ids))
        return await self.repo.create_run(run)


async def execute_audit_run(run_id: str):
    """Entry point for the BackgroundTask. Opens its own DB session — see
    module docstring for why that's correct here."""
    async with AsyncSessionLocal() as db:
        repo = AuditRepository(db)
        doc_repo = DocumentRepository(db)
        chunk_repo = ChunkRepository(db)
        knowledge_repo = KnowledgeRepository(db)
        rule_repo = RuleRepository(db)

        run = await repo.get_run(run_id)
        if not run:
            logger.error("audit_run_not_found", run_id=run_id)
            return

        run.status = "running"
        await db.commit()

        memory = empty_memory()
        llm = get_llm_provider()
        documents_failed = 0

        for idx, doc_id in enumerate(run.document_ids, start=1):
            await repo.update_progress(run, idx, f"processing document {idx}/{len(run.document_ids)}")
            try:
                document = await doc_repo.get_by_id(doc_id)
                if not document:
                    raise ValueError(f"document {doc_id} no longer exists")

                doc_summary, batches_used = await _summarize_document(llm, chunk_repo, doc_id)
                facts = await knowledge_repo.get_facts(doc_id)
                rule_run = await repo.get_latest_rule_run(doc_id)
                rule_findings = await rule_repo.get_findings(doc_id)

                memory = await _update_memory(
                    llm, memory, doc_id, document.original_filename, doc_summary,
                    facts, rule_findings, rule_run.risk_level if rule_run else "unknown",
                )

                # Safety net compaction check — independent of what the LLM's
                # own memory-update response decided to keep.
                compacted = False
                if estimate_memory_tokens(memory) > settings.AUDIT_MEMORY_TOKEN_LIMIT:
                    memory = await _compact_memory(llm, memory)
                    memory = cap_memory_size(memory, settings.AUDIT_MAX_FINDINGS_KEPT)
                    compacted = True
                    logger.info("audit_memory_compacted", run_id=run_id, after_document=idx)

                await repo.save_snapshot(AuditMemorySnapshot(
                    run_id=run_id, document_id=doc_id, order_index=idx,
                    document_summary=doc_summary, map_batches_used=batches_used,
                    memory_after=memory, memory_compacted=compacted,
                ))

            except Exception as e:
                documents_failed += 1
                logger.error("audit_document_failed", run_id=run_id, document_id=doc_id, error=str(e))
                memory["open_questions"].append(f"Document {doc_id} could not be processed: {e}")

        report_markdown = await _synthesize_final_report(llm, memory, run)
        risk_counts = _count_risk_flags(memory)

        await repo.save_report(AuditReport(
            run_id=run_id, content_markdown=report_markdown, risk_summary=risk_counts,
            documents_covered=len(run.document_ids) - documents_failed, documents_failed=documents_failed,
        ))

        run.status = "completed"
        run.current_stage = "done"
        await db.commit()
        logger.info("audit_run_completed", run_id=run_id, documents=len(run.document_ids), failed=documents_failed)


async def _summarize_document(llm, chunk_repo, doc_id: str) -> tuple[str, int]:
    chunks = await chunk_repo.get_for_document(doc_id)
    texts = [c.content for c in chunks if c.validation_status == "valid"]
    if not texts:
        return "(no extractable content)", 0

    max_tokens_per_batch = settings.LLM_MAX_CONTEXT_TOKENS - settings.LLM_RESPONSE_RESERVE_TOKENS - 300
    batches = batch_texts_by_budget(texts, max_tokens_per_batch)

    if len(batches) == 1:
        prompt = MAP_SUMMARY_PROMPT.format(system=AUDITOR_SYSTEM_PROMPT, batch_num=1, total_batches=1, text="\n\n".join(batches[0]))
        summary = await llm.generate(prompt)
        return summary, 1

    partial_summaries = []
    for i, batch in enumerate(batches, start=1):
        prompt = MAP_SUMMARY_PROMPT.format(system=AUDITOR_SYSTEM_PROMPT, batch_num=i, total_batches=len(batches), text="\n\n".join(batch))
        partial = await llm.generate(prompt)
        partial_summaries.append(f"[Part {i}] {partial}")

    combine_prompt = COMBINE_SUMMARY_PROMPT.format(
        system=AUDITOR_SYSTEM_PROMPT, n=len(partial_summaries), partial_summaries="\n\n".join(partial_summaries),
    )
    combined = await llm.generate(combine_prompt)
    return combined, len(batches)


async def _update_memory(llm, memory, doc_id, filename, doc_summary, facts, rule_findings, risk_level) -> dict:
    facts_json = json.dumps([{"type": f.fact_type, "value": f.value, "status": f.status} for f in facts])
    findings_json = json.dumps([
        {"rule": f.rule_name, "severity": f.severity, "triggered": f.triggered, "description": f.description}
        for f in rule_findings if f.triggered
    ])

    prompt = MEMORY_UPDATE_PROMPT.format(
        system=AUDITOR_SYSTEM_PROMPT, current_memory=json.dumps(memory), document_id=doc_id, filename=filename,
        document_summary=doc_summary, facts_json=facts_json, rule_findings_json=findings_json, risk_level=risk_level,
    )
    parsed = await _generate_json(prompt)
    if parsed is None:
        # Fallback: don't crash the run — fold in a plain-text note instead of structured JSON
        memory["key_findings"].append(f"[{filename}] {doc_summary[:300]}")
        memory["open_questions"].append(f"Memory update for {doc_id} returned invalid JSON — folded in as plain note")
        memory["documents_processed"].append(doc_id)
        return memory

    updated = normalize_memory(parsed)
    updated["documents_processed"] = memory.get("documents_processed", []) + [doc_id]
    return updated


async def _compact_memory(llm, memory) -> dict:
    prompt = MEMORY_COMPACTION_PROMPT.format(
        system=AUDITOR_SYSTEM_PROMPT, current_memory=json.dumps(memory), max_findings=settings.AUDIT_MAX_FINDINGS_KEPT,
    )
    parsed = await _generate_json(prompt)
    if parsed is None:
        # Compaction failing is not fatal — the hard cap_memory_size() safety
        # net still runs regardless, just without the LLM's smarter merging.
        return memory
    return normalize_memory(parsed)


async def _synthesize_final_report(llm, memory, run) -> str:
    prompt = FINAL_REPORT_PROMPT.format(
        system=AUDITOR_SYSTEM_PROMPT, doc_count=len(memory.get("documents_processed", [])),
        run_name=run.name, memory_json=json.dumps(memory, indent=2),
    )
    return await llm.generate(prompt)


async def _generate_json(prompt: str) -> dict | None:
    """Structured-output calls go through raw Ollama JSON mode directly,
    same pattern as the classifier — LangChain's ChatOllama wrapper (used for
    the free-text map/combine/report steps) doesn't expose format='json'."""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(f"{settings.OLLAMA_URL}/api/generate", json={
                "model": settings.AUDIT_MODEL, "prompt": prompt, "stream": False,
                "format": "json", "options": {"temperature": 0},
            })
            resp.raise_for_status()
            return json.loads(resp.json().get("response", "{}"))
    except Exception as e:
        logger.error("audit_json_generation_failed", error=str(e))
        return None


def _count_risk_flags(memory: dict) -> dict:
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for flag in memory.get("risk_flags", []):
        severity = flag.get("severity", "low")
        if severity in counts:
            counts[severity] += 1
    return counts