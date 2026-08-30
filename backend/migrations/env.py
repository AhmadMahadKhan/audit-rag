# ===== migrations/env.py =====

import sys
import asyncio
from pathlib import Path

# Make backend/ importable so "from app..." works
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# ---- Import app settings and Base ----
from app.core.config import settings
from app.db.session import Base

# ---- Import EVERY model module ----
# This ensures Base.metadata contains all tables.
from app.models import (
    user,
    activity,
    document,
    classification,
    parsing,
    canonical,
    metadata,
    knowledge,
    chunk,
    embedding,
    vector_sync,
    search,
    rule_engine,
    chat,
    search_management,
    evaluation,
    monitoring,
    audit_agent,
)

config = context.config

# Use the database URL from the application settings
config.set_main_option(
    "sqlalchemy.url",
    settings.database_url,
)

# IMPORTANT:
# Do NOT call fileConfig() here.
# Your alembic.ini does not contain the logging configuration
# expected by Python's fileConfig().

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in offline mode."""

    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named"
        },
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations using an existing database connection."""

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations against the database."""

    connectable = async_engine_from_config(
        config.get_section(
            config.config_ini_section,
            {}
        ),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(
            do_run_migrations
        )

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())