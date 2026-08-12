# ===== app/services/chat_service.py =====
import time
from typing import AsyncIterator
from app.chat.prompt_builder import build_prompt, PROMPT_VERSION
from app.chat.token_budget import fit_context_to_budget, trim_history
from app.chat.llm_providers.factory import get_llm_provider
from app.chat.citation_extractor import extract_citations
from app.chat.response_validator import validate_response
from app.chunking.token_utils import estimate_tokens
from app.services.reranking_service import RerankingService
from app.repositories.chat_repository import ChatRepository
from app.models.chat import Message
from app.services.activity_logger import log_activity
from app.core.config import settings
from app.core.exceptions import DocumentNotFound, AuthorizationError
from app.core.logging_config import logger

class ChatService:
    def __init__(self, db):
        self.db = db
        self.repo = ChatRepository(db)
        self.reranking = RerankingService(db)

    async def _prepare_turn(self, conversation_id: str, question: str, user_id: str, filters: dict | None):
        conversation = await self.repo.get_conversation(conversation_id)
        if not conversation:
            raise DocumentNotFound("Conversation not found")
        if conversation.user_id != user_id:
            raise AuthorizationError("Not your conversation")

        history_msgs = await self.repo.get_messages(conversation_id)
        history = [{"role": m.role, "content": m.content} for m in history_msgs]

        rerank_result = await self.reranking.retrieve_and_rerank(question, filters=filters, user_id=user_id)
        context_chunks = rerank_result["results"]

        budgeted_context = fit_context_to_budget(
            context_chunks, settings.LLM_MAX_CONTEXT_TOKENS - settings.LLM_RESPONSE_RESERVE_TOKENS - 500,
        )
        budgeted_history = trim_history(history, 500)

        prompt = build_prompt(question, budgeted_context, budgeted_history)
        return conversation, prompt, budgeted_context

    async def send_message(self, conversation_id: str, question: str, user_id: str,
                             filters: dict | None = None, provider_name: str | None = None) -> Message:
        t0 = time.perf_counter()
        conversation, prompt, context_chunks = await self._prepare_turn(conversation_id, question, user_id, filters)

        self.db.add(Message(conversation_id=conversation_id, role="user", content=question))
        await self.db.commit()

        llm = get_llm_provider(provider_name)
        response_text = await llm.generate(prompt)

        citations = extract_citations(response_text, context_chunks)
        status, confidence = validate_response(response_text, citations, context_chunks)

        assistant_msg = Message(
            conversation_id=conversation_id, role="assistant", content=response_text,
            citations=citations, confidence=confidence, validation_status=status,
            token_count=estimate_tokens(response_text),
        )
        assistant_msg = await self.repo.add_message(assistant_msg)

        if conversation.title == "New Conversation":
            conversation.title = question[:60]
        await self.db.commit()

        logger.info("chat_response_generated", conversation_id=conversation_id, status=status,
                     confidence=confidence, latency_ms=(time.perf_counter() - t0) * 1000)
        await log_activity(self.db, "ai_chat_request", user_id=user_id, status=status)
        return assistant_msg

    async def stream_message(self, conversation_id: str, question: str, user_id: str,
                               filters: dict | None = None, provider_name: str | None = None) -> AsyncIterator[str]:
        conversation, prompt, context_chunks = await self._prepare_turn(conversation_id, question, user_id, filters)

        self.db.add(Message(conversation_id=conversation_id, role="user", content=question))
        await self.db.commit()

        llm = get_llm_provider(provider_name)
        full_response = ""
        async for token in llm.stream(prompt):
            full_response += token
            yield token

        citations = extract_citations(full_response, context_chunks)
        status, confidence = validate_response(full_response, citations, context_chunks)
        await self.repo.add_message(Message(
            conversation_id=conversation_id, role="assistant", content=full_response,
            citations=citations, confidence=confidence, validation_status=status,
            token_count=estimate_tokens(full_response),
        ))
        if conversation.title == "New Conversation":
            conversation.title = question[:60]
            await self.db.commit()
        await log_activity(self.db, "ai_chat_request", user_id=user_id, status=status)

    async def regenerate(self, message_id: str, user_id: str) -> Message:
        from sqlalchemy import select
        from app.models.chat import Message as MessageModel
        result = await self.db.execute(select(MessageModel).where(MessageModel.id == message_id))
        msg = result.scalar_one_or_none()
        if not msg or msg.role != "assistant":
            raise DocumentNotFound("Assistant message not found")

        history = await self.repo.get_messages(msg.conversation_id)
        idx = next(i for i, m in enumerate(history) if m.id == message_id)
        question = history[idx - 1].content if idx > 0 else ""

        await self.db.delete(msg)
        await self.db.commit()
        return await self.send_message(msg.conversation_id, question, user_id)