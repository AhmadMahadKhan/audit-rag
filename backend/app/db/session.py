from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.orm import declarative_base

from app.core.config import settings


engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
)


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


Base = declarative_base()

# Import all models to ensure complete SQLAlchemy Base metadata mapping
import app.models.user
import app.models.document
import app.models.classification
import app.models.parsing
import app.models.canonical
import app.models.metadata
import app.models.knowledge
import app.models.rule_engine
import app.models.chunk
import app.models.embedding
import app.models.vector_sync
import app.models.chat
import app.models.search
import app.models.search_management
import app.models.evaluation
import app.models.monitoring
import app.models.activity


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session