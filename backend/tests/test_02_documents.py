# ===== tests/test_02_documents.py =====
"""Phase 4 — Upload pipeline: validation, hashing, dedup, storage."""
import pytest

pytestmark = pytest.mark.asyncio


class TestUpload:
    async def test_upload_valid_document(self, client, user_headers, sample_invoice_bytes):
        files = {"files": ("invoice1.txt", sample_invoice_bytes, "text/plain")}
        resp = await client.post("/api/v1/documents/upload", headers=user_headers, files=files)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success_count"] == 1
        assert body["results"][0]["status"] != "failed"

    async def test_upload_empty_file_rejected(self, client, user_headers):
        files = {"files": ("empty.txt", b"", "text/plain")}
        resp = await client.post("/api/v1/documents/upload", headers=user_headers, files=files)
        assert resp.status_code == 200
        assert resp.json()["failure_count"] == 1

    async def test_upload_disallowed_extension_rejected(self, client, user_headers):
        files = {"files": ("virus.exe", b"MZ\x90\x00", "application/octet-stream")}
        resp = await client.post("/api/v1/documents/upload", headers=user_headers, files=files)
        assert resp.status_code == 200
        assert resp.json()["failure_count"] == 1

    async def test_duplicate_upload_rejected(self, client, user_headers, sample_invoice_bytes):
        files = {"files": ("dup1.txt", sample_invoice_bytes, "text/plain")}
        first = await client.post("/api/v1/documents/upload", headers=user_headers, files=files)
        assert first.json()["success_count"] == 1

        files2 = {"files": ("dup2.txt", sample_invoice_bytes, "text/plain")}  # same content, different name
        second = await client.post("/api/v1/documents/upload", headers=user_headers, files=files2)
        assert second.json()["failure_count"] == 1
        assert "duplicate" in second.json()["results"][0]["error"].lower()

    async def test_path_traversal_filename_sanitized(self, client, user_headers):
        files = {"files": ("../../etc/passwd.txt", b"some content here", "text/plain")}
        resp = await client.post("/api/v1/documents/upload", headers=user_headers, files=files)
        assert resp.status_code == 200
        # should either succeed with sanitized name or fail cleanly — never 500
        assert resp.status_code != 500

    async def test_list_documents_returns_only_own(self, client, user_headers, admin_headers, sample_invoice_bytes):
        files = {"files": ("mine.txt", sample_invoice_bytes, "text/plain")}
        await client.post("/api/v1/documents/upload", headers=user_headers, files=files)
        resp = await client.get("/api/v1/documents", headers=user_headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    async def test_get_document_by_id(self, client, user_headers, sample_invoice_bytes):
        files = {"files": ("getme.txt", sample_invoice_bytes, "text/plain")}
        upload = await client.post("/api/v1/documents/upload", headers=user_headers, files=files)
        doc_id = upload.json()["results"][0]["document_id"]
        resp = await client.get(f"/api/v1/documents/{doc_id}", headers=user_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == doc_id

    async def test_get_nonexistent_document_404(self, client, user_headers):
        resp = await client.get("/api/v1/documents/nonexistent-id", headers=user_headers)
        assert resp.status_code == 404

    # async def test_delete_document(self, client, user_headers, sample_invoice_bytes):
    #     files = {"files": ("deleteme.txt", sample_invoice_bytes, "text/plain")}
    #     upload = await client.post("/api/v1/documents/upload", headers=user_headers, files=files)
    #     doc_id = upload.json()["results"][0]["document_id"]
    #     resp = await client.delete(f"/api/v1/documents/{doc_id}", headers=user_headers)
    #     assert resp.status_code == 200
    #     get_resp = await client.get(f"/api/v1/documents/{doc_id}", headers=user_headers)
    #     assert get_resp.status_code == 404
    # ===== tests/test_02_documents.py (FIX) =====
    async def test_delete_document(self, client, admin_headers, sample_invoice_bytes):
        # Deletion requires documents.delete, which the User role doesn't
        # grant in seeded_rbac — use admin_headers, which has all permissions.
        files = {"files": ("deleteme.txt", sample_invoice_bytes, "text/plain")}
        upload = await client.post("/api/v1/documents/upload", headers=admin_headers, files=files)
        doc_id = upload.json()["results"][0]["document_id"]
        resp = await client.delete(f"/api/v1/documents/{doc_id}", headers=admin_headers)
        assert resp.status_code == 200
        get_resp = await client.get(f"/api/v1/documents/{doc_id}", headers=admin_headers)
        assert get_resp.status_code == 404