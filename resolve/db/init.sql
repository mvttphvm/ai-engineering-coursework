-- Resolve — Postgres bootstrap.
-- docker-compose mounts this into /docker-entrypoint-initdb.d/ so it runs
-- once, the first time the database container starts.
-- The application creates its tables via SQLAlchemy (app/db.py); the one
-- thing SQLAlchemy cannot do first is enable the pgvector extension,
-- because the chunks table's `embedding vector(384)` column depends on it.

CREATE EXTENSION IF NOT EXISTS vector;

-- Sanity note for future scaling: once the corpus is large, add an
-- approximate index for the vector leg of hybrid search, e.g.
--   CREATE INDEX IF NOT EXISTS chunks_embedding_hnsw
--   ON chunks USING hnsw (embedding vector_cosine_ops);
