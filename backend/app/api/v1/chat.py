# ===== app/api/v1/chat.py =====
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.dependencies.auth import require_permission, get_current_user
from app.services.chat_service import ChatService
from app.repositories.chat_repository import ChatRepository
from app.schemas.chat import ConversationOut, MessageOut, SendMessageRequest, CreateConversationRequest
from app.core.exceptions import DocumentNotFound, AuthorizationError

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/conversations", response_model=ConversationOut)
async def create_conversation(payload: CreateConversationRequest, db: AsyncSession = Depends(get_db), user=Depends(require_permission("chat.use"))):
    return await ChatRepository(db).create_conversation(user.id, payload.title or "New Conversation")

@router.get("/conversations", response_model=list[ConversationOut])
async def list_conversations(db: AsyncSession = Depends(get_db), user=Depends(require_permission("chat.use"))):
    return await ChatRepository(db).list_conversations(user.id)

@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageOut])
async def get_messages(conversation_id: str, db: AsyncSession = Depends(get_db), user=Depends(require_permission("chat.use"))):
    conv = await ChatRepository(db).get_conversation(conversation_id)
    if not conv:
        raise DocumentNotFound("Conversation not found")
    if conv.user_id != user.id:
        raise AuthorizationError("Not your conversation")
    return await ChatRepository(db).get_messages(conversation_id)

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, db: AsyncSession = Depends(get_db), user=Depends(require_permission("chat.use"))):
    conv = await ChatRepository(db).get_conversation(conversation_id)
    if not conv:
        raise DocumentNotFound("Conversation not found")
    if conv.user_id != user.id:
        raise AuthorizationError("Not your conversation")
    await ChatRepository(db).delete_conversation(conv)
    return {"success": True}


@router.post("/conversations/{conversation_id}/messages", response_model=MessageOut)
async def send_message(conversation_id: str, payload: SendMessageRequest, db: AsyncSession = Depends(get_db), user=Depends(require_permission("chat.use"))):
    return await ChatService(db).send_message(
        conversation_id, payload.question, user.id, payload.filters, payload.document_ids, payload.provider,
    )

@router.post("/conversations/{conversation_id}/stream")
async def stream_message(conversation_id: str, payload: SendMessageRequest, db: AsyncSession = Depends(get_db), user=Depends(require_permission("chat.use"))):
    service = ChatService(db)
    return StreamingResponse(
        service.stream_message(conversation_id, payload.question, user.id, payload.filters, payload.document_ids, payload.provider),
        media_type="text/event-stream",
    )

@router.post("/messages/{message_id}/regenerate", response_model=MessageOut)
async def regenerate(message_id: str, db: AsyncSession = Depends(get_db), user=Depends(require_permission("chat.use"))):
    return await ChatService(db).regenerate(message_id, user.id)