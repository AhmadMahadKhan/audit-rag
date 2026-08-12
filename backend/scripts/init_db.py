# ===== scripts/init_db.py =====
"""One-time dev bootstrap: creates all tables directly from the ORM models,
bypassing Alembic. NOT for production — use real migrations there. Run:
python -m scripts.init_db
"""
import asyncio


from app.models import (
    user, activity, document, classification, parsing, canonical, metadata,
    knowledge, chunk, embedding, vector_sync, search, rule_engine, chat,
    search_management, evaluation, monitoring,
)
from app.db.session import engine, Base


async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("All tables created.")


if __name__ == "__main__":
    asyncio.run(init_models())