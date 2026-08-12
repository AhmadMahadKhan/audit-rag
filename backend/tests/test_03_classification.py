# ===== tests/test_03_classification.py =====
"""Phase 5 — Classification: rule-based routing + confidence thresholds."""
import pytest
import pytest_asyncio
pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def uploaded_invoice(client, user_headers, sample_invoice_bytes):
    files = {"files": ("invoice-INV-001.txt", sample_invoice_bytes, "text/plain")}
    resp = await client.post("/api/v1/documents/upload", headers=user_headers, files=files)
    return resp.json()["results"][0]["document_id"]


class TestClassification:
    async def test_filename_based_classification_detects_invoice(self, client, user_headers, uploaded_invoice):
        resp = await client.post(f"/api/v1/classification/{uploaded_invoice}/classify", headers=user_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["document_type"] == "invoice"
        assert body["confidence"] > 0

    async def test_unknown_document_type_for_ambiguous_filename(self, client, user_headers, sample_invoice_bytes):
        files = {"files": ("randomfile123.txt", sample_invoice_bytes, "text/plain")}
        upload = await client.post("/api/v1/documents/upload", headers=user_headers, files=files)
        doc_id = upload.json()["results"][0]["document_id"]
        resp = await client.post(f"/api/v1/classification/{doc_id}/classify", headers=user_headers)
        assert resp.status_code == 200
        # filename gives no signal -> falls back toward unknown or low confidence
        assert resp.json()["document_type"] in ("unknown",) or resp.json()["confidence"] < 0.7

    async def test_manual_reclassification_overrides(self, client, user_headers, admin_headers, uploaded_invoice):
        await client.post(f"/api/v1/classification/{uploaded_invoice}/classify", headers=user_headers)
        resp = await client.post(f"/api/v1/classification/{uploaded_invoice}/reclassify", headers=admin_headers,
                                   json={"document_type": "contract"})
        assert resp.status_code == 200
        assert resp.json()["document_type"] == "contract"
        assert resp.json()["method"] == "manual"

    async def test_reclassify_with_invalid_type_rejected(self, client, admin_headers, uploaded_invoice):
        resp = await client.post(f"/api/v1/classification/{uploaded_invoice}/reclassify", headers=admin_headers,
                                   json={"document_type": "not_a_real_type"})
        assert resp.status_code == 422

    async def test_supported_types_endpoint(self, client, user_headers):
        resp = await client.get("/api/v1/classification/types/supported", headers=user_headers)
        assert resp.status_code == 200
        assert "invoice" in resp.json()["types"]

    async def test_classification_history_tracks_reclassifications(self, client, user_headers, admin_headers, uploaded_invoice):
        await client.post(f"/api/v1/classification/{uploaded_invoice}/classify", headers=user_headers)
        await client.post(f"/api/v1/classification/{uploaded_invoice}/reclassify", headers=admin_headers,
                            json={"document_type": "receipt"})
        resp = await client.get(f"/api/v1/classification/{uploaded_invoice}/history", headers=user_headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 2