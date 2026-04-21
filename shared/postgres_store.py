"""Postgres + pgvector long-term memory store.

Drop-in alternative to ``shared.semantic_store.SemanticStore`` when
``POSTGRES_URL`` is set (Supabase or self-hosted). Implements the same
tiny subset of the LangGraph BaseStore surface: ``put``, ``search``,
``get``, ``delete`` — search does semantic similarity via pgvector when
a query is provided, otherwise a plain namespace scan.

Schema (created at first instance construction if missing)::

    CREATE EXTENSION IF NOT EXISTS vector;
    CREATE TABLE IF NOT EXISTS arquimedes_memory (
        id          TEXT PRIMARY KEY,
        namespace   TEXT NOT NULL,
        key         TEXT NOT NULL,
        content     TEXT NOT NULL,
        metadata    JSONB NOT NULL DEFAULT '{}'::jsonb,
        embedding   vector(1536) NOT NULL,
        updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS arquimedes_memory_ns_idx
        ON arquimedes_memory (namespace);
    CREATE INDEX IF NOT EXISTS arquimedes_memory_embed_idx
        ON arquimedes_memory USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100);

Requires the pgvector extension (native on Supabase). Dimensionality is
``1536`` by default (OpenAI text-embedding-3-small); override with
``POSTGRES_EMBED_DIM`` when switching to a different embedder.
"""

from __future__ import annotations

import json
import os
from typing import Any, Iterable

from shared.store_types import StoreRecord, namespace_key as _ns


class PostgresSemanticStore:
    """pgvector-backed long-term memory store."""

    def __init__(
        self,
        conn_string: str | None = None,
        table_name: str = "arquimedes_memory",
        embedding_dim: int | None = None,
        embedding_function=None,
    ):
        try:
            import psycopg2
            import psycopg2.extras  # noqa: F401
        except Exception as e:  # pragma: no cover
            raise RuntimeError(
                "psycopg2-binary is required for PostgresSemanticStore"
            ) from e

        self._psycopg2 = psycopg2
        self._conn_string = (
            conn_string
            or os.getenv("POSTGRES_URL")
            or os.getenv("SUPABASE_DB_URL")
        )
        if not self._conn_string:
            raise RuntimeError(
                "PostgresSemanticStore requires POSTGRES_URL or SUPABASE_DB_URL"
            )

        self._table = table_name
        self._dim = embedding_dim or int(os.getenv("POSTGRES_EMBED_DIM", "1536"))

        # Lazy: if no embedder is injected, use the shared factory so all
        # stores agree on the model.
        if embedding_function is None:
            from arquimedes.rag.embeddings import get_embeddings
            self._embed = get_embeddings()
        else:
            self._embed = embedding_function

        self._ensure_schema()

    def _connect(self):
        return self._psycopg2.connect(self._conn_string)

    def _ensure_schema(self) -> None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self._table} (
                    id TEXT PRIMARY KEY,
                    namespace TEXT NOT NULL,
                    key TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                    embedding vector({self._dim}) NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )
            cur.execute(
                f"CREATE INDEX IF NOT EXISTS {self._table}_ns_idx "
                f"ON {self._table} (namespace);"
            )
            cur.execute(
                f"CREATE INDEX IF NOT EXISTS {self._table}_embed_idx "
                f"ON {self._table} USING ivfflat (embedding vector_cosine_ops) "
                f"WITH (lists = 100);"
            )

    def _embed_one(self, text: str) -> list[float]:
        return self._embed.embed_query(text)

    @staticmethod
    def _vec_literal(values: Iterable[float]) -> str:
        # pgvector accepts a textual vector literal: '[0.1, 0.2, ...]'
        return "[" + ",".join(f"{float(x):.8f}" for x in values) + "]"

    # ── BaseStore-compatible surface ──────────────────────────────────
    def put(self, namespace: tuple[str, ...], key: str, value: dict[str, Any]) -> None:
        content = value.get("content") or str(value)
        metadata = {k: v for k, v in value.items() if k != "content"}
        emb = self._embed_one(content)

        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO {self._table}
                    (id, namespace, key, content, metadata, embedding, updated_at)
                VALUES (%s, %s, %s, %s, %s::jsonb, %s::vector, NOW())
                ON CONFLICT (id) DO UPDATE SET
                    content = EXCLUDED.content,
                    metadata = EXCLUDED.metadata,
                    embedding = EXCLUDED.embedding,
                    updated_at = NOW();
                """,
                (
                    f"{_ns(namespace)}::{key}",
                    _ns(namespace),
                    key,
                    content,
                    json.dumps(metadata),
                    self._vec_literal(emb),
                ),
            )

    def search(
        self,
        namespace: tuple[str, ...],
        query: str | None = None,
        limit: int = 5,
    ) -> list[StoreRecord]:
        ns = _ns(namespace)
        with self._connect() as conn, conn.cursor() as cur:
            if query:
                q_emb = self._vec_literal(self._embed_one(query))
                cur.execute(
                    f"""
                    SELECT key, content, metadata
                    FROM {self._table}
                    WHERE namespace = %s
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s;
                    """,
                    (ns, q_emb, limit),
                )
            else:
                cur.execute(
                    f"""
                    SELECT key, content, metadata
                    FROM {self._table}
                    WHERE namespace = %s
                    ORDER BY updated_at DESC
                    LIMIT %s;
                    """,
                    (ns, limit),
                )
            rows = cur.fetchall()

        out: list[StoreRecord] = []
        for key, content, meta in rows:
            value = {"content": content}
            if meta:
                value.update(meta)
            out.append(StoreRecord(namespace=namespace, key=key, value=value))
        return out

    def get(self, namespace: tuple[str, ...], key: str) -> StoreRecord | None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                f"SELECT content, metadata FROM {self._table} WHERE id = %s;",
                (f"{_ns(namespace)}::{key}",),
            )
            row = cur.fetchone()
        if not row:
            return None
        content, meta = row
        value = {"content": content}
        if meta:
            value.update(meta)
        return StoreRecord(namespace=namespace, key=key, value=value)

    def delete(self, namespace: tuple[str, ...], key: str) -> None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                f"DELETE FROM {self._table} WHERE id = %s;",
                (f"{_ns(namespace)}::{key}",),
            )
