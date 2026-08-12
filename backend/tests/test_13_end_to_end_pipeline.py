# ===== tests/test_13_end_to_end_pipeline.py =====
"""
Full-pipeline integration test: upload -> classify -> parse -> canonicalize
-> metadata -> extraction -> rules -> chunk -> embed -> index -> retrieve
-> chat, asserting each stage's output feeds correctly into the next and
that a deliberately-broken invoice gets flagged by the rule engine while
still completing the pipeline.
"""
import pytest

pytestmark = pytest.mark.asyncio


class TestFullDocumentLifecycle:
    async def test_clean_invoice_flows_through_entire_pipeline(self, client, user_headers, admin_headers, sample_invoice_bytes):
        # 1. Upload
        files = {"files": ("e2e-invoice-INV.txt", sample_invoice_bytes, "text/plain")}
        upload = await client.post("/api/v1/documents/upload", headers=user_headers, files=files)
        assert upload.status_code == 200
        doc_id = upload.json()["results"][0]["document_id"]

        # 2. Classify
        classify = await client.post(f"/api/v1/classification/{doc_id}/classify", headers=user_headers)
        assert classify.status_code == 200
        assert classify.json()["document_type"] == "invoice"

        # 3. Parse
        parse = await client.post(f"/api/v1/parsing/{doc_id}/parse", headers=user_headers)
        assert parse.status_code == 200

        # 4. Canonicalize
        canonical = await client.post(f"/api/v1/canonical/{doc_id}/build", headers=user_headers)
        assert canonical.status_code == 200
        assert canonical.json()["validation_status"] == "valid"

        # 5. Metadata extraction
        metadata = await client.post(f"/api/v1/metadata/{doc_id}/extract", headers=user_headers)
        assert metadata.status_code == 200

        # 6. Entity/fact extraction
        extraction = await client.post(f"/api/v1/extraction/{doc_id}/extract", headers=user_headers)
        assert extraction.status_code == 200
        assert extraction.json()["fact_count"] >= 1

        # 7. Rule engine
        await client.post("/api/v1/rules/seed", headers=admin_headers)
        rules = await client.post(f"/api/v1/rules/{doc_id}/execute", headers=user_headers)
        assert rules.status_code == 200
        assert rules.json()["risk_level"] == "low"  # clean invoice should be low risk

        # 8. Chunking
        chunks = await client.post(f"/api/v1/chunks/{doc_id}/generate", headers=user_headers)
        assert chunks.status_code == 200
        assert chunks.json()["chunk_count"] >= 1

        # 9. Embeddings
        embeddings = await client.post(f"/api/v1/embeddings/{doc_id}/generate", headers=user_headers, json={"types": ["text"]})
        assert embeddings.status_code == 200
        assert embeddings.json()["failed_count"] == 0

        # 10. Indexing
        index = await client.post(f"/api/v1/vectorstore/{doc_id}/index", headers=user_headers)
        assert index.status_code == 200
        assert index.json()["indexed"] >= 1

        # 11. Retrieval
        search = await client.post("/api/v1/retrieval/hybrid", headers=user_headers,
                                     json={"query": "what is the invoice total", "top_k": 5, "use_rewrite": False})
        assert search.status_code == 200

        # 12. Chat
        conv = await client.post("/api/v1/chat/conversations", headers=user_headers, json={})
        chat = await client.post(f"/api/v1/chat/conversations/{conv.json()['id']}/messages", headers=user_headers,
                                   json={"question": "What is the total on this invoice?"})
        assert chat.status_code == 200
        assert chat.json()["content"]

        # 13. Viewer bundle sanity check — everything should be visible together
        bundle = await client.get(f"/api/v1/viewer/{doc_id}/bundle", headers=user_headers)
        assert bundle.status_code == 200
        b = bundle.json()
        assert b["document"]["processing_status"] in ("indexed", "rules_evaluated", "chunked", "embedded")
        assert len(b["facts"]) >= 1
        assert len(b["chunks"]) >= 1

    async def test_broken_invoice_flagged_by_rules_but_pipeline_completes(self, client, user_headers, admin_headers, sample_invoice_text):
        broken_text = sample_invoice_text.replace("Total: 165.00", "Total: 99999.00")  # breaks math + triggers high-value rule
        files = {"files": ("e2e-broken-invoice-INV.txt", broken_text.encode(), "text/plain")}
        upload = await client.post("/api/v1/documents/upload", headers=user_headers, files=files)
        doc_id = upload.json()["results"][0]["document_id"]

        await client.post(f"/api/v1/classification/{doc_id}/classify", headers=user_headers)
        await client.post(f"/api/v1/parsing/{doc_id}/parse", headers=user_headers)
        await client.post(f"/api/v1/canonical/{doc_id}/build", headers=user_headers)
        await client.post(f"/api/v1/metadata/{doc_id}/extract", headers=user_headers)
        await client.post(f"/api/v1/extraction/{doc_id}/extract", headers=user_headers)

        await client.post("/api/v1/rules/seed", headers=admin_headers)
        rules_resp = await client.post(f"/api/v1/rules/{doc_id}/execute", headers=user_headers)
        assert rules_resp.status_code == 200
        run = rules_resp.json()
        assert run["rules_triggered"] >= 1
        assert run["risk_level"] in ("medium", "high", "critical")

        findings = (await client.get(f"/api/v1/rules/{doc_id}/findings", headers=user_headers)).json()
        assert any(f["rule_key"] == "total_equals_subtotal_plus_tax" and f["triggered"] for f in findings)

        # pipeline should still be able to proceed past a flagged (not blocked) document
        chunk_resp = await client.post(f"/api/v1/chunks/{doc_id}/generate", headers=user_headers)
        assert chunk_resp.status_code == 200

    async def test_pipeline_stage_ordering_enforced(self, client, user_headers, sample_invoice_bytes):
        """Confirms downstream stages fail cleanly (not 500) if upstream stage was skipped."""
        files = {"files": ("order-test-invoice.txt", sample_invoice_bytes, "text/plain")}
        upload = await client.post("/api/v1/documents/upload", headers=user_headers, files=files)
        doc_id = upload.json()["results"][0]["document_id"]

        # Try chunking before canonical build exists
        resp = await client.post(f"/api/v1/chunks/{doc_id}/generate", headers=user_headers)
        assert resp.status_code in (400, 404, 422)
        assert resp.status_code != 500

    async def test_document_isolation_across_users(self, client, user_headers, admin_headers, sample_invoice_bytes):
        """A second user's document should not be visible/actionable by the first."""
        files = {"files": ("isolated-invoice.txt", sample_invoice_bytes, "text/plain")}
        upload = await client.post("/api/v1/documents/upload", headers=admin_headers, files=files)
        doc_id = upload.json()["results"][0]["document_id"]

        resp = await client.get(f"/api/v1/documents/{doc_id}", headers=user_headers)
        assert resp.status_code == 403


class TestConcurrentDocumentProcessing:
    async def test_multiple_documents_processed_independently(self, client, user_headers, sample_invoice_text):
        doc_ids = []
        for i in range(3):
            text = sample_invoice_text.replace("INV-2026-0042", f"INV-2026-{1000+i}")
            files = {"files": (f"concurrent-{i}.txt", text.encode(), "text/plain")}
            upload = await client.post("/api/v1/documents/upload", headers=user_headers, files=files)
            assert upload.status_code == 200
            doc_ids.append(upload.json()["results"][0]["document_id"])

        assert len(set(doc_ids)) == 3  # all distinct, no collision

        for doc_id in doc_ids:
            classify = await client.post(f"/api/v1/classification/{doc_id}/classify", headers=user_headers)
            assert classify.status_code == 200