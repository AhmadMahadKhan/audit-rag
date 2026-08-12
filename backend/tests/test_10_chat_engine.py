# ===== tests/test_10_chat_engine.py =====
"""Phase 15 — Chat / RAG orchestration (LLM calls mocked)."""
import pytest

pytestmark = pytest.mark.asyncio


class TestChatConversations:
    async def test_create_conversation(self, client, user_headers):
        resp = await client.post("/api/v1/chat/conversations", headers=user_headers, json={"title": "My Chat"})
        assert resp.status_code == 200
        assert resp.json()["title"] == "My Chat"

    async def test_list_conversations_scoped_to_user(self, client, user_headers, admin_headers):
        await client.post("/api/v1/chat/conversations", headers=user_headers, json={})
        resp = await client.get("/api/v1/chat/conversations", headers=user_headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

        admin_resp = await client.get("/api/v1/chat/conversations", headers=admin_headers)
        admin_ids = {c["id"] for c in admin_resp.json()}
        user_ids = {c["id"] for c in resp.json()}
        assert admin_ids.isdisjoint(user_ids) or admin_resp.json() == []

    async def test_send_message_returns_grounded_answer(self, client, user_headers):
        conv = await client.post("/api/v1/chat/conversations", headers=user_headers, json={})
        conv_id = conv.json()["id"]
        resp = await client.post(f"/api/v1/chat/conversations/{conv_id}/messages", headers=user_headers,
                                   json={"question": "What is the invoice total?"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["role"] == "assistant"
        assert body["content"]
        assert body["validation_status"] in ("valid", "low_confidence", "refused")

    async def test_get_messages_after_send(self, client, user_headers):
        conv = await client.post("/api/v1/chat/conversations", headers=user_headers, json={})
        conv_id = conv.json()["id"]
        await client.post(f"/api/v1/chat/conversations/{conv_id}/messages", headers=user_headers,
                            json={"question": "hello"})
        resp = await client.get(f"/api/v1/chat/conversations/{conv_id}/messages", headers=user_headers)
        assert resp.status_code == 200
        roles = [m["role"] for m in resp.json()]
        assert "user" in roles and "assistant" in roles

    async def test_cannot_access_other_users_conversation(self, client, user_headers, admin_headers):
        conv = await client.post("/api/v1/chat/conversations", headers=user_headers, json={})
        conv_id = conv.json()["id"]
        resp = await client.get(f"/api/v1/chat/conversations/{conv_id}/messages", headers=admin_headers)
        assert resp.status_code == 403

    async def test_delete_conversation(self, client, user_headers):
        conv = await client.post("/api/v1/chat/conversations", headers=user_headers, json={})
        conv_id = conv.json()["id"]
        resp = await client.delete(f"/api/v1/chat/conversations/{conv_id}", headers=user_headers)
        assert resp.status_code == 200

    async def test_regenerate_creates_new_assistant_message(self, client, user_headers):
        conv = await client.post("/api/v1/chat/conversations", headers=user_headers, json={})
        conv_id = conv.json()["id"]
        first = await client.post(f"/api/v1/chat/conversations/{conv_id}/messages", headers=user_headers,
                                    json={"question": "What's the total?"})
        msg_id = first.json()["id"]
        resp = await client.post(f"/api/v1/chat/messages/{msg_id}/regenerate", headers=user_headers)
        assert resp.status_code == 200
        assert resp.json()["role"] == "assistant"


class TestPromptBuilder:
    def test_prompt_includes_context_and_question(self):
        from app.chat.prompt_builder import build_prompt
        prompt = build_prompt("What is X?", [{"document_id": "d1", "pages": [1], "content": "X is 42."}], [])
        assert "What is X?" in prompt
        assert "X is 42." in prompt
        assert "d1" in prompt

    def test_prompt_handles_empty_context(self):
        from app.chat.prompt_builder import build_prompt
        prompt = build_prompt("What is X?", [], [])
        assert "no relevant context found" in prompt.lower()


class TestCitationExtraction:
    def test_extracts_single_citation(self):
        from app.chat.citation_extractor import extract_citations
        text = "The total is 165 [Doc: doc1, Page: 1]."
        citations = extract_citations(text, [{"document_id": "doc1", "chunk_id": "c1", "section_name": "Totals"}])
        assert len(citations) == 1
        assert citations[0]["document_id"] == "doc1"
        assert citations[0]["chunk_id"] == "c1"

    def test_deduplicates_repeated_citations(self):
        from app.chat.citation_extractor import extract_citations
        text = "A [Doc: doc1, Page: 1]. B [Doc: doc1, Page: 1]."
        citations = extract_citations(text, [])
        assert len(citations) == 1

    def test_no_citations_in_plain_text(self):
        from app.chat.citation_extractor import extract_citations
        assert extract_citations("no markers here", []) == []


class TestResponseValidator:
    def test_refusal_phrase_detected(self):
        from app.chat.response_validator import validate_response
        status, conf = validate_response("I don't have enough information in the documents to answer this.", [], [])
        assert status == "refused"
        assert conf == 0.0

    def test_valid_response_with_citations(self):
        from app.chat.response_validator import validate_response
        status, conf = validate_response(
            "The total is 165 [Doc: doc1, Page: 1].",
            [{"document_id": "doc1", "page": "1"}],
            [{"final_score": 0.9}],
        )
        assert status == "valid"
        assert conf > 0

    def test_no_citations_lowers_confidence(self):
        from app.chat.response_validator import validate_response
        status, conf = validate_response("The total is 165.", [], [{"final_score": 0.9}])
        assert status == "low_confidence"


class TestTokenBudget:
    def test_fit_context_respects_budget(self):
        from app.chat.token_budget import fit_context_to_budget
        chunks = [{"content": "word " * 100} for _ in range(10)]
        result = fit_context_to_budget(chunks, max_tokens=50)
        assert len(result) < 10

    def test_trim_history_keeps_recent_messages(self):
        from app.chat.token_budget import trim_history
        history = [{"role": "user", "content": f"message {i}"} for i in range(20)]
        result = trim_history(history, max_tokens=1000)
        assert result[-1]["content"] == "message 19"