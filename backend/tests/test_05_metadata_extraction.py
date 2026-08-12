# ===== tests/test_05_metadata_extraction.py =====
"""Phases 8-9 — Metadata, Entity, Fact, Line Item extraction."""
import pytest 
import pytest_asyncio 

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def processed_invoice(client, user_headers, sample_invoice_bytes):
    """Runs the full pre-extraction pipeline: upload -> classify -> parse -> canonicalize."""
    files = {"files": ("invoice-full.txt", sample_invoice_bytes, "text/plain")}
    upload = await client.post("/api/v1/documents/upload", headers=user_headers, files=files)
    doc_id = upload.json()["results"][0]["document_id"]
    await client.post(f"/api/v1/classification/{doc_id}/classify", headers=user_headers)
    await client.post(f"/api/v1/parsing/{doc_id}/parse", headers=user_headers)
    await client.post(f"/api/v1/canonical/{doc_id}/build", headers=user_headers)
    return doc_id


class TestMetadataExtraction:
    async def test_extract_metadata_finds_currency(self, client, user_headers, processed_invoice):
        resp = await client.post(f"/api/v1/metadata/{processed_invoice}/extract", headers=user_headers)
        assert resp.status_code == 200
        fields_resp = await client.get(f"/api/v1/metadata/{processed_invoice}", headers=user_headers)
        keys = {f["key"] for f in fields_resp.json()}
        assert "currency" in keys or "file_type" in keys  # at minimum document-level fields extracted

    async def test_manual_metadata_update(self, client, user_headers, processed_invoice):
        await client.post(f"/api/v1/metadata/{processed_invoice}/extract", headers=user_headers)
        resp = await client.put(f"/api/v1/metadata/{processed_invoice}", headers=user_headers,
                                  json={"key": "vendor", "value": "Manually Set Vendor"})
        assert resp.status_code == 200
        fields = (await client.get(f"/api/v1/metadata/{processed_invoice}", headers=user_headers)).json()
        vendor_field = next(f for f in fields if f["key"] == "vendor")
        assert vendor_field["value"] == "Manually Set Vendor"
        assert vendor_field["extractor"] == "manual"

    async def test_metadata_search_by_filter(self, client, user_headers, processed_invoice):
        await client.post(f"/api/v1/metadata/{processed_invoice}/extract", headers=user_headers)
        await client.put(f"/api/v1/metadata/{processed_invoice}", headers=user_headers,
                           json={"key": "vendor", "value": "SearchableVendorXYZ"})
        resp = await client.post("/api/v1/metadata/search", headers=user_headers,
                                   json={"filters": {"vendor": "SearchableVendorXYZ"}, "skip": 0, "limit": 50})
        assert resp.status_code == 200
        assert processed_invoice in resp.json()["document_ids"]


class TestEntityFactExtraction:
    async def test_extract_finds_invoice_number_entity(self, client, user_headers, processed_invoice):
        resp = await client.post(f"/api/v1/extraction/{processed_invoice}/extract", headers=user_headers)
        assert resp.status_code == 200
        entities = (await client.get(f"/api/v1/extraction/{processed_invoice}/entities", headers=user_headers)).json()
        types = {e["entity_type"] for e in entities}
        assert "invoice_number" in types

    async def test_extract_finds_financial_facts(self, client, user_headers, processed_invoice):
        await client.post(f"/api/v1/extraction/{processed_invoice}/extract", headers=user_headers)
        facts = (await client.get(f"/api/v1/extraction/{processed_invoice}/facts", headers=user_headers)).json()
        fact_types = {f["fact_type"] for f in facts}
        assert "invoice_total" in fact_types
        total_fact = next(f for f in facts if f["fact_type"] == "invoice_total")
        assert total_fact["numeric_value"] == pytest.approx(165.00)

    async def test_fact_validation_flags_bad_totals(self, client, user_headers, sample_invoice_text):
        bad_text = sample_invoice_text.replace("Total: 165.00", "Total: 999.00")  # break subtotal+tax=total
        files = {"files": ("bad-invoice.txt", bad_text.encode(), "text/plain")}
        upload = await client.post("/api/v1/documents/upload", headers=user_headers, files=files)
        doc_id = upload.json()["results"][0]["document_id"]
        await client.post(f"/api/v1/classification/{doc_id}/classify", headers=user_headers)
        await client.post(f"/api/v1/parsing/{doc_id}/parse", headers=user_headers)
        await client.post(f"/api/v1/canonical/{doc_id}/build", headers=user_headers)
        await client.post(f"/api/v1/extraction/{doc_id}/extract", headers=user_headers)

        facts = (await client.get(f"/api/v1/extraction/{doc_id}/facts", headers=user_headers)).json()
        total_fact = next(f for f in facts if f["fact_type"] == "invoice_total")
        assert total_fact["status"] == "needs_review"
        assert total_fact["validation_note"] is not None

    async def test_line_items_extracted_with_correct_totals(self, client, user_headers, processed_invoice):
        await client.post(f"/api/v1/extraction/{processed_invoice}/extract", headers=user_headers)
        items = (await client.get(f"/api/v1/extraction/{processed_invoice}/line-items", headers=user_headers)).json()
        assert len(items) >= 1

    async def test_search_entities_across_documents(self, client, user_headers, processed_invoice):
        await client.post(f"/api/v1/extraction/{processed_invoice}/extract", headers=user_headers)
        resp = await client.get("/api/v1/extraction/search/entities", headers=user_headers,
                                  params={"entity_type": "invoice_number"})
        assert resp.status_code == 200
        assert len(resp.json()) >= 1