# ===== tests/test_14_search_ui_and_viewer.py =====
"""Phases 16-17 — Document viewer aggregation + search UI (history, saved searches)."""
import pytest
import pytest_asyncio

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def fully_processed_doc(client, user_headers, admin_headers, sample_invoice_bytes):
    files = {"files": ("viewer-test-invoice.txt", sample_invoice_bytes, "text/plain")}
    upload = await client.post("/api/v1/documents/upload", headers=user_headers, files=files)
    doc_id = upload.json()["results"][0]["document_id"]
    await client.post(f"/api/v1/classification/{doc_id}/classify", headers=user_headers)
    await client.post(f"/api/v1/parsing/{doc_id}/parse", headers=user_headers)
    await client.post(f"/api/v1/canonical/{doc_id}/build", headers=user_headers)
    await client.post(f"/api/v1/metadata/{doc_id}/extract", headers=user_headers)
    await client.post(f"/api/v1/extraction/{doc_id}/extract", headers=user_headers)
    await client.post(f"/api/v1/chunks/{doc_id}/generate", headers=user_headers)
    return doc_id


# class TestDocumentViewer:
#     async def test_bundle_forbidden_for_other_user(self, client, admin_headers, fully_processed_doc):
#         resp = await client.get(f"/api/v1/viewer/{fully_processed_doc}/bundle", headers=admin_headers)
#         assert resp.status_code == 403
#     async def test_bundle_contains_all_sections(self, client, user_headers, fully_processed_doc):
#         resp = await client.get(f"/api/v1/viewer/{fully_processed_doc}/bundle", headers=user_headers)
#         assert resp.status_code == 200
#         body = resp.json()
#         for key in ("document", "metadata", "entities", "facts", "chunks", "embedding_status"):
#             assert key in body
# ===== tests/test_14_search_ui_and_viewer.py (FIX) =====
class TestDocumentViewer:
    async def test_bundle_contains_all_sections(self, client, user_headers, fully_processed_doc):
        resp = await client.get(f"/api/v1/viewer/{fully_processed_doc}/bundle", headers=user_headers)
        assert resp.status_code == 200
        body = resp.json()
        for key in ("document", "metadata", "entities", "facts", "chunks", "embedding_status"):
            assert key in body

    async def test_bundle_forbidden_for_other_user(self, client, user_headers, admin_headers, sample_invoice_bytes):
        # Isolation only holds against users WITHOUT documents.delete — admin
        # intentionally bypasses ownership (same as the documents API), so
        # use admin as the doc owner and the plain user (lacking that
        # permission) as the unauthorized viewer.
        files = {"files": ("admin-owned-doc.txt", sample_invoice_bytes, "text/plain")}
        upload = await client.post("/api/v1/documents/upload", headers=admin_headers, files=files)
        doc_id = upload.json()["results"][0]["document_id"]

        resp = await client.get(f"/api/v1/viewer/{doc_id}/bundle", headers=user_headers)
        assert resp.status_code == 403

    async def test_search_within_document_finds_match(self, client, user_headers, fully_processed_doc):
        resp = await client.get(f"/api/v1/viewer/{fully_processed_doc}/search", headers=user_headers, params={"q": "Acme"})
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    async def test_citation_resolution_returns_chunk_detail(self, client, user_headers, fully_processed_doc):
        chunks_resp = await client.get(f"/api/v1/chunks/{fully_processed_doc}", headers=user_headers)
        chunk_id = chunks_resp.json()[0]["id"]
        resp = await client.get(f"/api/v1/viewer/{fully_processed_doc}/citation/{chunk_id}", headers=user_headers)
        assert resp.status_code == 200
        assert resp.json()["chunk_id"] == chunk_id


class TestSearchUI:
    async def test_hybrid_mode_search(self, client, user_headers, fully_processed_doc):
        resp = await client.post("/api/v1/search", headers=user_headers,
                                   json={"query": "invoice total", "mode": "hybrid", "top_k": 5})
        assert resp.status_code == 200

    async def test_entity_mode_search(self, client, user_headers, fully_processed_doc):
        resp = await client.post("/api/v1/search", headers=user_headers,
                                   json={"query": "INV", "mode": "entity", "top_k": 5})
        assert resp.status_code == 200

    async def test_search_history_recorded(self, client, user_headers, fully_processed_doc):
        await client.post("/api/v1/retrieval/hybrid", headers=user_headers,
                            json={"query": "history test query", "top_k": 5, "use_rewrite": False})
        resp = await client.get("/api/v1/search/history", headers=user_headers)
        assert resp.status_code == 200
        assert any(h["query"] == "history test query" for h in resp.json())

    async def test_save_and_run_saved_search(self, client, user_headers):
        save_resp = await client.post("/api/v1/search/saved", headers=user_headers,
                                        json={"name": "My Saved", "query": "total amount", "search_mode": "hybrid"})
        assert save_resp.status_code == 200
        search_id = save_resp.json()["id"]

        run_resp = await client.post(f"/api/v1/search/saved/{search_id}/run", headers=user_headers)
        assert run_resp.status_code == 200

    async def test_delete_saved_search(self, client, user_headers):
        save_resp = await client.post("/api/v1/search/saved", headers=user_headers,
                                        json={"name": "ToDelete", "query": "x", "search_mode": "hybrid"})
        search_id = save_resp.json()["id"]
        del_resp = await client.delete(f"/api/v1/search/saved/{search_id}", headers=user_headers)
        assert del_resp.status_code == 200
        listing = (await client.get("/api/v1/search/saved", headers=user_headers)).json()
        assert search_id not in {s["id"] for s in listing}

    async def test_suggestions_match_prefix(self, client, user_headers):
        await client.post("/api/v1/retrieval/hybrid", headers=user_headers,
                            json={"query": "prefix matching test", "top_k": 5, "use_rewrite": False})
        resp = await client.get("/api/v1/search/suggestions", headers=user_headers, params={"q": "prefix"})
        assert resp.status_code == 200