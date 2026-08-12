# ===== tests/test_08_embeddings_vectorstore.py =====
"""Phases 11-12 — Embedding generation + Qdrant indexing (mocked)."""
import pytest
import pytest_asyncio

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def chunked_invoice(client, user_headers, sample_invoice_bytes):
    files = {"files": ("embed-invoice-INV.txt", sample_invoice_bytes, "text/plain")}
    upload = await client.post("/api/v1/documents/upload", headers=user_headers, files=files)
    doc_id = upload.json()["results"][0]["document_id"]
    await client.post(f"/api/v1/classification/{doc_id}/classify", headers=user_headers)
    await client.post(f"/api/v1/parsing/{doc_id}/parse", headers=user_headers)
    await client.post(f"/api/v1/canonical/{doc_id}/build", headers=user_headers)
    await client.post(f"/api/v1/chunks/{doc_id}/generate", headers=user_headers)
    return doc_id


class TestEmbeddings:
    async def test_generate_text_embeddings(self, client, user_headers, chunked_invoice):
        resp = await client.post(f"/api/v1/embeddings/{chunked_invoice}/generate", headers=user_headers,
                                   json={"types": ["text"]})
        assert resp.status_code == 200
        assert resp.json()["total_count"] >= 1
        assert resp.json()["failed_count"] == 0

    async def test_embeddings_have_correct_dimension(self, client, user_headers, chunked_invoice):
        await client.post(f"/api/v1/embeddings/{chunked_invoice}/generate", headers=user_headers, json={"types": ["text"]})
        resp = await client.get(f"/api/v1/embeddings/{chunked_invoice}", headers=user_headers)
        assert resp.status_code == 200
        records = resp.json()
        assert all(r["vector_dimension"] == 768 for r in records)
        assert all(r["status"] == "valid" for r in records)

    async def test_regenerating_deactivates_old_embeddings(self, client, user_headers, chunked_invoice):
        await client.post(f"/api/v1/embeddings/{chunked_invoice}/generate", headers=user_headers, json={"types": ["text"]})
        first_count = len((await client.get(f"/api/v1/embeddings/{chunked_invoice}", headers=user_headers)).json())
        await client.post(f"/api/v1/embeddings/{chunked_invoice}/generate", headers=user_headers, json={"types": ["text"]})
        second_active = (await client.get(f"/api/v1/embeddings/{chunked_invoice}", headers=user_headers)).json()
        # only the newest generation's records should be active
        assert len(second_active) == first_count

    async def test_available_models_endpoint(self, client, user_headers):
        resp = await client.get("/api/v1/embeddings/models/available", headers=user_headers)
        assert resp.status_code == 200
        assert "ollama" in resp.json()["providers"]


class TestEmbeddingValidator:
    def test_rejects_dimension_mismatch(self):
        from app.embeddings.validator import validate_vector
        status, issue = validate_vector([0.1, 0.2], expected_dim=768)
        assert status == "invalid"

    def test_rejects_zero_vector(self):
        from app.embeddings.validator import validate_vector
        status, issue = validate_vector([0.0] * 768, expected_dim=768)
        assert status == "invalid"

    def test_accepts_valid_vector(self):
        from app.embeddings.validator import validate_vector
        status, issue = validate_vector([0.1] * 768, expected_dim=768)
        assert status == "valid"

    def test_rejects_nan_values(self):
        from app.embeddings.validator import validate_vector
        vec = [0.1] * 767 + [float("nan")]
        status, issue = validate_vector(vec, expected_dim=768)
        assert status == "invalid"


class TestVectorStoreIndexing:
    async def test_index_document_after_embeddings(self, client, user_headers, chunked_invoice):
        await client.post(f"/api/v1/embeddings/{chunked_invoice}/generate", headers=user_headers, json={"types": ["text"]})
        resp = await client.post(f"/api/v1/vectorstore/{chunked_invoice}/index", headers=user_headers)
        assert resp.status_code == 200
        assert resp.json()["indexed"] >= 1

    async def test_vector_search_returns_results_after_indexing(self, client, user_headers, chunked_invoice):
        await client.post(f"/api/v1/embeddings/{chunked_invoice}/generate", headers=user_headers, json={"types": ["text"]})
        await client.post(f"/api/v1/vectorstore/{chunked_invoice}/index", headers=user_headers)
        resp = await client.post("/api/v1/vectorstore/search", headers=user_headers,
                                   json={"query": "invoice total", "embedding_type": "text", "top_k": 5})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_collection_stats_endpoint(self, client, admin_headers, chunked_invoice):
        resp = await client.get("/api/v1/vectorstore/stats", headers=admin_headers)
        assert resp.status_code == 200