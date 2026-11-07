"""Chunk storage behind one interface, two backends:

- `InMemoryStore` — tests, offline evals, small demos. Zero setup.
- `PostgresStore` — production: SQLAlchemy over Postgres + pgvector
  (see app/db.py and db/init.sql).

Retrieval ranking runs over `all_chunks()` — for the knowledge-base scale
this project targets that is honest and simple; the Postgres schema stores
embeddings in a pgvector column so the vector leg can be pushed into SQL
(`ORDER BY embedding <=> query`) as the corpus grows.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class ChunkRecord:
    chunk_id: str
    source: str
    title: str
    text: str
    embedding: list[float]
    metadata: dict = field(default_factory=dict)


class ChunkStore(Protocol):
    def add(self, records: list[ChunkRecord]) -> int: ...
    def all_chunks(self) -> list[ChunkRecord]: ...
    def count(self) -> int: ...
    def clear_source(self, source: str) -> None: ...


class InMemoryStore:
    def __init__(self) -> None:
        self._records: dict[str, ChunkRecord] = {}

    def add(self, records: list[ChunkRecord]) -> int:
        for record in records:
            self._records[record.chunk_id] = record
        return len(records)

    def all_chunks(self) -> list[ChunkRecord]:
        return list(self._records.values())

    def count(self) -> int:
        return len(self._records)

    def clear_source(self, source: str) -> None:
        self._records = {
            k: v for k, v in self._records.items() if v.source != source
        }


class PostgresStore:
    """SQLAlchemy/pgvector-backed store. Requires a reachable Postgres —
    constructed lazily by the app only when DATABASE_URL points at one."""

    def __init__(self, database_url: str) -> None:
        from app.db import make_engine, make_session_factory

        self._engine = make_engine(database_url)
        self._session_factory = make_session_factory(self._engine)

    def init_schema(self) -> None:
        from app.db import init_schema

        init_schema(self._engine)

    def add(self, records: list[ChunkRecord]) -> int:
        from app.db import ChunkRow

        with self._session_factory() as session:
            for record in records:
                session.merge(ChunkRow(
                    chunk_id=record.chunk_id,
                    source=record.source,
                    title=record.title,
                    text=record.text,
                    embedding=record.embedding,
                    meta=record.metadata,
                ))
            session.commit()
        return len(records)

    def all_chunks(self) -> list[ChunkRecord]:
        from app.db import ChunkRow

        with self._session_factory() as session:
            rows = session.query(ChunkRow).all()
            return [ChunkRecord(
                chunk_id=r.chunk_id,
                source=r.source,
                title=r.title,
                text=r.text,
                embedding=list(r.embedding) if r.embedding is not None else [],
                metadata=r.meta or {},
            ) for r in rows]

    def count(self) -> int:
        from app.db import ChunkRow

        with self._session_factory() as session:
            return session.query(ChunkRow).count()

    def clear_source(self, source: str) -> None:
        from app.db import ChunkRow

        with self._session_factory() as session:
            session.query(ChunkRow).filter(ChunkRow.source == source).delete()
            session.commit()
