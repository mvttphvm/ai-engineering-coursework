"""Postgres + pgvector schema (SQLAlchemy).

The matching SQL bootstrap lives in db/init.sql (mounted into the Postgres
container by docker-compose) and enables the `vector` extension before any
table exists. `init_schema()` below does the same for non-Docker setups.
"""
from __future__ import annotations

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, String, Text, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

EMBEDDING_DIM = 384  # all-MiniLM-L6-v2; keep in sync with EMBEDDING_DIM env


class Base(DeclarativeBase):
    pass


class ChunkRow(Base):
    __tablename__ = "chunks"

    chunk_id: Mapped[str] = mapped_column(String(512), primary_key=True)
    source: Mapped[str] = mapped_column(String(512), index=True)
    title: Mapped[str] = mapped_column(String(512), default="")
    text: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM))
    meta: Mapped[dict] = mapped_column(JSON, default=dict)


def make_engine(database_url: str):
    # psycopg (v3) driver: postgresql+psycopg://...
    return create_engine(database_url, pool_pre_ping=True)


def make_session_factory(engine):
    return sessionmaker(bind=engine, expire_on_commit=False)


def init_schema(engine) -> None:
    """Create the pgvector extension and all tables (idempotent)."""
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(engine)
