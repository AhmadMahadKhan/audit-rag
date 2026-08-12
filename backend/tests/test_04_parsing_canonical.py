# ===== tests/test_04_parsing_canonical.py =====
"""Phases 6-7 — Parsing and Canonical Document Model."""
import pytest
import pytest_asyncio

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def uploaded_html(client, user_headers):
    html = b"<html><body><h1>Test Doc</h1><p>Some paragraph content here.</p></body></html>"
    files = {"files": ("test.html", html, "text/html")}
    resp = await client.post("/api/v1/documents/upload", headers=user_headers, files=files)
    return resp.json()["results"][0]["document_id"]


class TestParsingCanonical:
    async def test_html_parsing_extracts_blocks(self, client, user_headers, uploaded_html):
        resp = await client.post(f"/api/v1/parsing/{uploaded_html}/parse", headers=user_headers)
        assert resp.status_code == 200
        assert resp.json()["parser_name"] == "html_parser"
        assert resp.json()["status"] in ("completed", "needs_review")

    async def test_get_parsing_result_contains_raw_text(self, client, user_headers, uploaded_html):
        await client.post(f"/api/v1/parsing/{uploaded_html}/parse", headers=user_headers)
        resp = await client.get(f"/api/v1/parsing/{uploaded_html}", headers=user_headers)
        assert resp.status_code == 200
        assert "Test Doc" in resp.json()["raw_text"] or "paragraph" in resp.json()["raw_text"]

    async def test_parsing_unparsed_document_404(self, client, user_headers, uploaded_html):
        resp = await client.get("/api/v1/parsing/nonexistent-doc-id", headers=user_headers)
        assert resp.status_code == 404

    async def test_canonical_build_requires_parsing_first(self, client, user_headers, uploaded_html):
        resp = await client.post(f"/api/v1/canonical/{uploaded_html}/build", headers=user_headers)
        assert resp.status_code in (400, 404, 422)

    async def test_canonical_build_after_parsing(self, client, user_headers, uploaded_html):
        await client.post(f"/api/v1/parsing/{uploaded_html}/parse", headers=user_headers)
        resp = await client.post(f"/api/v1/canonical/{uploaded_html}/build", headers=user_headers)
        assert resp.status_code == 200
        assert resp.json()["validation_status"] in ("valid", "invalid")

    async def test_canonical_export_returns_full_json(self, client, user_headers, uploaded_html):
        await client.post(f"/api/v1/parsing/{uploaded_html}/parse", headers=user_headers)
        await client.post(f"/api/v1/canonical/{uploaded_html}/build", headers=user_headers)
        resp = await client.get(f"/api/v1/canonical/{uploaded_html}/export", headers=user_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "blocks" in body and "info" in body

    async def test_canonical_schema_version_endpoint(self, client, user_headers):
        resp = await client.get("/api/v1/canonical/schema/version", headers=user_headers)
        assert resp.status_code == 200
        assert resp.json()["schema_version"] == "1.0"


class TestCanonicalValidator:
    """Unit-level: exercise the validator directly, not just via API."""

    def test_validator_flags_block_referencing_missing_page(self):
        from app.canonical.schema import CanonicalDocument, DocumentInfo, PageModel, BlockModel, ProcessingInfo
        from app.canonical.validator import validate_canonical_document
        from datetime import datetime, timezone

        doc = CanonicalDocument(
            info=DocumentInfo(document_id="d1", file_name="f.pdf", file_type="pdf", mime_type="application/pdf",
                               file_size=10, file_hash="abc", parser_name="p", parser_version="1", page_count=1,
                               processed_at=datetime.now(timezone.utc)),
            pages=[PageModel(page_number=1)],
            blocks=[BlockModel(block_id="b1", type="paragraph", text="x", page=2, order=0)],  # page 2 doesn't exist
            tables=[], images=[], raw_text="x", processing=ProcessingInfo(),
        )
        issues = validate_canonical_document(doc)
        assert any("missing page" in i for i in issues)

    def test_validator_passes_consistent_document(self):
        from app.canonical.schema import CanonicalDocument, DocumentInfo, PageModel, BlockModel, ProcessingInfo
        from app.canonical.validator import validate_canonical_document
        from datetime import datetime, timezone

        doc = CanonicalDocument(
            info=DocumentInfo(document_id="d1", file_name="f.pdf", file_type="pdf", mime_type="application/pdf",
                               file_size=10, file_hash="abc", parser_name="p", parser_version="1", page_count=1,
                               processed_at=datetime.now(timezone.utc)),
            pages=[PageModel(page_number=1)],
            blocks=[BlockModel(block_id="b1", type="paragraph", text="x", page=1, order=0)],
            tables=[], images=[], raw_text="x", processing=ProcessingInfo(),
        )
        assert validate_canonical_document(doc) == []