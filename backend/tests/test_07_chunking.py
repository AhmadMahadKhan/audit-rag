# ===== tests/test_07_chunking.py =====
"""Phase 10 — Chunking strategies."""
import pytest
import pytest_asyncio

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def canonicalized_invoice(client, user_headers, sample_invoice_bytes):
    files = {"files": ("chunk-invoice-INV.txt", sample_invoice_bytes, "text/plain")}
    upload = await client.post("/api/v1/documents/upload", headers=user_headers, files=files)
    doc_id = upload.json()["results"][0]["document_id"]
    await client.post(f"/api/v1/classification/{doc_id}/classify", headers=user_headers)
    await client.post(f"/api/v1/parsing/{doc_id}/parse", headers=user_headers)
    await client.post(f"/api/v1/canonical/{doc_id}/build", headers=user_headers)
    return doc_id


class TestChunkingAPI:
    async def test_generate_chunks_for_invoice(self, client, user_headers, canonicalized_invoice):
        resp = await client.post(f"/api/v1/chunks/{canonicalized_invoice}/generate", headers=user_headers)
        assert resp.status_code == 200
        assert resp.json()["chunk_count"] >= 1

    async def test_list_chunks_have_valid_status(self, client, user_headers, canonicalized_invoice):
        await client.post(f"/api/v1/chunks/{canonicalized_invoice}/generate", headers=user_headers)
        resp = await client.get(f"/api/v1/chunks/{canonicalized_invoice}", headers=user_headers)
        assert resp.status_code == 200
        chunks = resp.json()
        assert all(c["validation_status"] in ("valid", "needs_review", "invalid") for c in chunks)

    async def test_chunks_linked_prev_next(self, client, user_headers, canonicalized_invoice):
        await client.post(f"/api/v1/chunks/{canonicalized_invoice}/generate", headers=user_headers)
        chunks = (await client.get(f"/api/v1/chunks/{canonicalized_invoice}", headers=user_headers)).json()
        if len(chunks) > 1:
            assert chunks[0]["next_chunk_id"] == chunks[1]["id"]
            assert chunks[1]["prev_chunk_id"] == chunks[0]["id"]

    async def test_rechunk_regenerates_chunks(self, client, user_headers, canonicalized_invoice):
        first = await client.post(f"/api/v1/chunks/{canonicalized_invoice}/generate", headers=user_headers)
        second = await client.post(f"/api/v1/chunks/{canonicalized_invoice}/rechunk", headers=user_headers)
        assert second.status_code == 200
        assert second.json()["chunk_count"] == first.json()["chunk_count"]


class TestChunkerUnits:
    def test_generic_chunker_produces_nonempty_chunks(self):
        from app.chunking.generic_chunker import GenericChunker
        from app.canonical.schema import CanonicalDocument, DocumentInfo, PageModel, BlockModel, ProcessingInfo
        from datetime import datetime, timezone

        doc = CanonicalDocument(
            info=DocumentInfo(document_id="d1", file_name="f", file_type="txt", mime_type="text/plain",
                               file_size=1, file_hash="h", parser_name="p", parser_version="1", page_count=1,
                               processed_at=datetime.now(timezone.utc)),
            pages=[PageModel(page_number=1)],
            blocks=[BlockModel(block_id="b1", type="paragraph", text="Some content here.", page=1, order=0)],
            tables=[], images=[], raw_text="Some content here.", processing=ProcessingInfo(),
        )
        chunks = GenericChunker().chunk(doc)
        assert len(chunks) >= 1
        assert all(c.content.strip() for c in chunks)

    def test_chunk_validator_rejects_empty(self):
        from app.chunking.validator import validate_chunk
        from app.chunking.schema import ChunkCandidate
        status, issue = validate_chunk(ChunkCandidate(chunk_type="generic", content="   "))
        assert status == "invalid"

    def test_chunk_validator_accepts_normal_content(self):
        from app.chunking.validator import validate_chunk
        from app.chunking.schema import ChunkCandidate
        status, issue = validate_chunk(ChunkCandidate(chunk_type="generic", content="A reasonably sized chunk of text."))
        assert status == "valid"

    def test_deduplicate_removes_identical_chunks(self):
        from app.chunking.validator import deduplicate
        from app.chunking.schema import ChunkCandidate
        chunks = [ChunkCandidate(chunk_type="generic", content="same text"), ChunkCandidate(chunk_type="generic", content="same text")]
        assert len(deduplicate(chunks)) == 1