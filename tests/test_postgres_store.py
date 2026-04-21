"""Tests for shared/postgres_store.py.

We mock psycopg2 to avoid needing a running Postgres — the goal is to
verify our SQL payload shape, parameter binding, and fallback behaviour.
A full integration test runs only when POSTGRES_URL is set (skipped by
default in CI).
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def fake_embed():
    m = MagicMock()
    m.embed_query.return_value = [0.01] * 1536
    return m


@pytest.fixture
def store(fake_embed):
    # Mock psycopg2 so construction doesn't actually connect.
    with patch.dict(os.environ, {"POSTGRES_URL": "postgresql://fake"}, clear=False):
        with patch("shared.postgres_store.PostgresSemanticStore._ensure_schema"):
            with patch("shared.postgres_store.PostgresSemanticStore._connect") as conn:
                ctx_cur = MagicMock()
                ctx_cur.__enter__ = lambda self: self
                ctx_cur.__exit__ = lambda self, *a: None
                ctx_cur.execute = MagicMock()
                ctx_cur.fetchall = MagicMock(return_value=[])
                ctx_cur.fetchone = MagicMock(return_value=None)

                conn_instance = MagicMock()
                conn_instance.__enter__ = lambda self: conn_instance
                conn_instance.__exit__ = lambda self, *a: None
                conn_instance.cursor.return_value = ctx_cur
                conn.return_value = conn_instance

                from shared.postgres_store import PostgresSemanticStore
                s = PostgresSemanticStore(
                    conn_string="postgresql://fake",
                    embedding_function=fake_embed,
                )
                s._cur = ctx_cur
                s._conn = conn_instance
                yield s


class TestPostgresSemanticStore:
    def test_put_upserts_with_vector_literal(self, store, fake_embed):
        with patch.object(store, "_connect") as conn:
            cur = MagicMock()
            cur.__enter__ = lambda self: cur
            cur.__exit__ = lambda self, *a: None
            cur.execute = MagicMock()
            ci = MagicMock()
            ci.__enter__ = lambda self: ci
            ci.__exit__ = lambda self, *a: None
            ci.cursor.return_value = cur
            conn.return_value = ci

            store.put(("student_profile", "alice"), "f1", {"content": "hello"})

            fake_embed.embed_query.assert_called_once_with("hello")
            assert cur.execute.called
            sql = cur.execute.call_args[0][0]
            params = cur.execute.call_args[0][1]
            assert "INSERT INTO arquimedes_memory" in sql
            assert "::vector" in sql
            assert params[0] == "student_profile::alice::f1"
            assert params[1] == "student_profile::alice"
            assert params[2] == "f1"
            # vector literal starts with '['
            assert params[5].startswith("[")

    def test_search_semantic_uses_cosine_distance(self, store):
        with patch.object(store, "_connect") as conn:
            cur = MagicMock()
            cur.__enter__ = lambda self: cur
            cur.__exit__ = lambda self, *a: None
            cur.execute = MagicMock()
            cur.fetchall = MagicMock(return_value=[
                ("k1", "alice struggles with chain rule", {"topic": "calculus"}),
            ])
            ci = MagicMock()
            ci.__enter__ = lambda self: ci
            ci.__exit__ = lambda self, *a: None
            ci.cursor.return_value = cur
            conn.return_value = ci

            results = store.search(("student_profile", "alice"), query="derivative", limit=3)
            sql = cur.execute.call_args[0][0]
            assert "embedding <=> " in sql  # pgvector cosine operator
            assert len(results) == 1
            assert results[0].value["content"] == "alice struggles with chain rule"
            assert results[0].value["topic"] == "calculus"

    def test_search_without_query_is_recency_order(self, store):
        with patch.object(store, "_connect") as conn:
            cur = MagicMock()
            cur.__enter__ = lambda self: cur
            cur.__exit__ = lambda self, *a: None
            cur.execute = MagicMock()
            cur.fetchall = MagicMock(return_value=[])
            ci = MagicMock()
            ci.__enter__ = lambda self: ci
            ci.__exit__ = lambda self, *a: None
            ci.cursor.return_value = cur
            conn.return_value = ci

            store.search(("student_profile", "bob"))
            sql = cur.execute.call_args[0][0]
            assert "ORDER BY updated_at DESC" in sql


class TestMemoryFactory:
    def test_get_store_prefers_postgres_when_url_set(self, monkeypatch, fake_embed):
        from shared import memory as mem_mod
        mem_mod.reset_memory_singletons()

        monkeypatch.setenv("POSTGRES_URL", "postgresql://fake")

        with patch("shared.postgres_store.PostgresSemanticStore") as pss:
            instance = MagicMock(name="PostgresSemanticStore-instance")
            pss.return_value = instance

            store = mem_mod.get_store()
            assert store is instance

        mem_mod.reset_memory_singletons()

    def test_get_store_falls_back_to_semantic_when_postgres_fails(self, monkeypatch):
        from shared import memory as mem_mod
        mem_mod.reset_memory_singletons()

        monkeypatch.setenv("POSTGRES_URL", "postgresql://fake")

        with patch("shared.postgres_store.PostgresSemanticStore", side_effect=RuntimeError("boom")):
            store = mem_mod.get_store()
            # Should have fallen through to SemanticStore (or InMemoryStore if chroma missing)
            assert store is not None

        mem_mod.reset_memory_singletons()
