# ===== tests/conftest.py (REPLACE fixtures below — rest of file unchanged) =====
"""
Isolation fix: use an in-memory SQLite engine created FRESH per test
function (not per session), with tables created before each test and
dropped after. This eliminates cross-test UNIQUE constraint collisions
without needing manual cleanup logic per test.
"""
import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("ENVIROMENT", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("STORAGE_LOCAL_PATH", "./test_storage")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
from datetime import date, timedelta

from app.main import app
from app.db.session import Base, get_db
from app.core.security import hash_password
from app.models.user import User, Role, Permission
# ===== tests/conftest.py (ADD near the top, after the app import) =====

# Force-import every model module so all tables register on Base.metadata
# before create_all() runs. Importing app.main pulls in routers -> services
# -> repositories, which SHOULD cascade-import every model — but relying on
# that transitive chain is fragile (one missed import anywhere breaks every
# DB-touching test identically, which is exactly what's happening). Import
# explicitly instead.
# ===== tests/conftest.py (REPLACE the model-import block) =====

# Force-import every model module so all tables register on Base.metadata
# before create_all() runs. Using `from X import Y` form deliberately —
# `import app.models.user` would rebind the name `app` in this module to
# the top-level package instead of the FastAPI instance imported below,
# which is exactly what caused dependency_overrides to disappear.
from app.models import user as _m_user            # noqa: F401
from app.models import activity as _m_activity     # noqa: F401
from app.models import document as _m_document     # noqa: F401
from app.models import classification as _m_classification  # noqa: F401
from app.models import parsing as _m_parsing       # noqa: F401
from app.models import canonical as _m_canonical   # noqa: F401
from app.models import metadata as _m_metadata     # noqa: F401
from app.models import knowledge as _m_knowledge   # noqa: F401
from app.models import chunk as _m_chunk           # noqa: F401
from app.models import embedding as _m_embedding   # noqa: F401
from app.models import vector_sync as _m_vector_sync  # noqa: F401
from app.models import search as _m_search         # noqa: F401
from app.models import rule_engine as _m_rule_engine  # noqa: F401
from app.models import chat as _m_chat             # noqa: F401
from app.models import search_management as _m_search_management  # noqa: F401
from app.models import evaluation as _m_evaluation  # noqa: F401
from app.models import monitoring as _m_monitoring  # noqa: F401
LIVE = os.environ.get("LIVE_INTEGRATION") == "1"


# @pytest_asyncio.fixture
# async def db_session():
#     """Fresh in-memory DB per test — StaticPool keeps the single :memory:
#     connection alive for the fixture's lifetime; engine is disposed after."""
#     engine = create_async_engine(
#         "sqlite+aiosqlite:///:memory:",
#         echo=False,
#         connect_args={"check_same_thread": False},
#         poolclass=StaticPool,
#     )
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)

#     session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
#     async with session_factory() as session:
#         yield session

#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.drop_all)
#     await engine.dispose()

@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    # Redirect the app's global AsyncSessionLocal (used by exception handlers
    # and anything else that opens its own session outside the get_db DI
    # chain) to this same test engine — otherwise it silently points at a
    # separate, empty database.
    import app.db.session as db_session_module
    original_session_local = db_session_module.AsyncSessionLocal
    db_session_module.AsyncSessionLocal = session_factory

    async with session_factory() as session:
        yield session

    db_session_module.AsyncSessionLocal = original_session_local

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest_asyncio.fixture(autouse=True)
async def override_db(db_session):
    async def _get_db():
        yield db_session
    app.dependency_overrides[get_db] = _get_db
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ---- everything below (seeded_rbac, admin_user, normal_user, tokens,
#      sample_invoice_*, mock_external_services, auth_header) is unchanged
#      from the original conftest.py ----


@pytest_asyncio.fixture
async def seeded_rbac(db_session):
    """Minimal RBAC seed: Admin role with all perms + a User role."""
    perms = ["documents.read", "documents.upload", "documents.delete", "users.read", "users.update",
              "chat.use", "analytics.read", "rules.manage", "settings.manage"]
    perm_objs = {p: Permission(code=p) for p in perms}
    for p in perm_objs.values():
        db_session.add(p)
    await db_session.flush()

    admin_role = Role(name="Admin", permissions=list(perm_objs.values()))
    user_role = Role(name="User", permissions=[perm_objs["documents.read"], perm_objs["documents.upload"], perm_objs["chat.use"]])
    db_session.add_all([admin_role, user_role])
    await db_session.flush()
    await db_session.commit()
    return {"admin_role": admin_role, "user_role": user_role, "perms": perm_objs}


@pytest_asyncio.fixture
async def admin_user(db_session, seeded_rbac):
    user = User(email="admin@test.com", hashed_password=hash_password("Admin123!"),
                 full_name="Admin", roles=[seeded_rbac["admin_role"]])
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def normal_user(db_session, seeded_rbac):
    user = User(email="user@test.com", hashed_password=hash_password("User1234!"),
                 full_name="Test User", roles=[seeded_rbac["user_role"]])
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_token(client, admin_user):
    resp = await client.post("/api/v1/auth/login", json={"email": "admin@test.com", "password": "Admin123!"})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def user_token(client, normal_user):
    resp = await client.post("/api/v1/auth/login", json={"email": "user@test.com", "password": "User1234!"})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def user_headers(user_token):
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture
# def sample_invoice_text():
#     return """INVOICE
# Invoice No: INV-2026-0042
# Vendor: Acme Supplies Inc
# Bill To: Contoso Corp
# Invoice Date: 01/15/2026
# Due Date: 02/15/2026

# Item          Qty   Unit Price   Total
# Widget A      10    5.00         50.00
# Widget B      5     20.00        100.00

# Subtotal: 150.00
# Tax: 15.00
# Total: 165.00
# Currency: USD
# """
def sample_invoice_text():
    invoice_date = date.today() - timedelta(days=30)
    due_date = date.today() + timedelta(days=1)  # not far enough forward to look suspicious, but still future-due is normal
    return f"""INVOICE
Invoice No: INV-2026-0042
Vendor: Acme Supplies Inc
Bill To: Contoso Corp
Invoice Date: {invoice_date.strftime('%m/%d/%Y')}
Due Date: {due_date.strftime('%m/%d/%Y')}

Item          Qty   Unit Price   Total
Widget A      10    5.00         50.00
Widget B      5     20.00        100.00

Subtotal: 150.00
Tax: 15.00
Total: 165.00
Currency: USD
"""

@pytest.fixture
def sample_invoice_bytes(sample_invoice_text):
    return sample_invoice_text.encode("utf-8")


@pytest.fixture(autouse=True)
def mock_external_services(monkeypatch):
    """Auto-applied unless LIVE_INTEGRATION=1 — stubs Ollama embeddings/LLM
    and Qdrant so the suite is hermetic and fast."""
    if LIVE:
        return

    async def fake_embed(self, texts):
        return [[0.1] * 768 for _ in texts]

    async def fake_generate(self, prompt):
        return "The invoice total is 165.00 [Doc: doc1, Page: 1]."

    async def fake_stream(self, prompt):
        for tok in ["The ", "invoice ", "total ", "is ", "165.00."]:
            yield tok

    async def fake_score(self, query, documents):
        return [0.9 - i * 0.05 for i in range(len(documents))]

    monkeypatch.setattr("app.embeddings.ollama_provider.OllamaEmbeddingProvider.embed", fake_embed)
    monkeypatch.setattr("app.chat.llm_providers.ollama_provider.OllamaLLMProvider.generate", fake_generate)
    monkeypatch.setattr("app.chat.llm_providers.ollama_provider.OllamaLLMProvider.stream", fake_stream)

    # class FakeVectorStore:
    #     def __init__(self):
    #         self._points = {}

    #     async def ensure_collection(self, name, dimension):
    #         self._points.setdefault(name, [])

    #     async def upsert(self, collection, points):
    #         self._points.setdefault(collection, []).extend(points)

    #     async def search(self, collection, vector, top_k, filters=None):
    #         pts = self._points.get(collection, [])[:top_k]
    #         return [{"id": p["id"], "score": 0.85, "payload": p["payload"]} for p in pts]

    #     async def delete(self, collection, point_ids):
    #         pass

    #     async def get_collection_stats(self, collection):
    #         return {"vectors_count": len(self._points.get(collection, [])), "points_count": len(self._points.get(collection, [])),
    #                  "status": "green", "segments_count": 1}

    #     async def list_collections(self):
    #         return list(self._points.keys())

    #     async def delete_collection(self, name):
    #         self._points.pop(name, None)

    # fake_store = FakeVectorStore()
    # monkeypatch.setattr("app.vectorstore.factory.get_vector_store", lambda: fake_store)

# ===== tests/conftest.py (REPLACE the Qdrant mocking section) =====

    class FakeVectorStore:
        def __init__(self, *args, **kwargs):
            self._points = {}

        async def ensure_collection(self, name, dimension):
            self._points.setdefault(name, [])

        async def upsert(self, collection, points):
            self._points.setdefault(collection, []).extend(points)

        async def search(self, collection, vector, top_k, filters=None):
            pts = self._points.get(collection, [])[:top_k]
            return [{"id": p["id"], "score": 0.85, "payload": p["payload"]} for p in pts]

        async def delete(self, collection, point_ids):
            pass

        async def get_collection_stats(self, collection):
            return {"vectors_count": len(self._points.get(collection, [])), "points_count": len(self._points.get(collection, [])),
                     "status": "green", "segments_count": 1}

        async def list_collections(self):
            return list(self._points.keys())

        async def delete_collection(self, name):
            self._points.pop(name, None)

    fake_store = FakeVectorStore()

    # Patch the module-level singleton cache directly, AND patch the
    # QdrantProvider class itself so any fresh instantiation returns the
    # fake — covers both the cached-singleton path and any code that
    # constructs QdrantProvider() directly.
    import app.vectorstore.factory as factory_module
    factory_module._instance = fake_store
    monkeypatch.setattr(factory_module, "get_vector_store", lambda: fake_store)
    monkeypatch.setattr("app.vectorstore.qdrant_provider.QdrantProvider", lambda: fake_store)

def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}