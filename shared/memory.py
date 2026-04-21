"""Memory primitives for all agents.

Two persistence layers, both singletons so every agent in the same process
shares state:

- **Checkpointer** — conversation history per ``thread_id``. Defaults to
  SqliteSaver (persistent across restarts) when ``SQLITE_CHECKPOINT_PATH``
  is set; falls back to MemorySaver otherwise.
- **Store** — long-term learner profile per ``(namespace, user_id)``.
  When ``MEMORY_BACKEND=semantic`` (default when chromadb is installed),
  returns a SemanticStore backed by Chroma; otherwise InMemoryStore.

To switch to Postgres + pgvector (Supabase) in production, flip
``MEMORY_BACKEND=postgres`` and point to the Supabase connection string
(planned extension; see docs/arquimedes.md).
"""

from __future__ import annotations

import os

from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore

# Optional persistent backends
try:
    from langgraph.checkpoint.sqlite import SqliteSaver
    _SQLITE_AVAILABLE = True
except Exception:  # pragma: no cover
    _SQLITE_AVAILABLE = False

try:
    from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
    import aiosqlite  # noqa: F401
    _AIOSQLITE_AVAILABLE = True
except Exception:  # pragma: no cover
    _AIOSQLITE_AVAILABLE = False

try:
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    _POSTGRES_AVAILABLE = True
except Exception:  # pragma: no cover
    _POSTGRES_AVAILABLE = False

try:
    from shared.semantic_store import SemanticStore
    _SEMANTIC_AVAILABLE = True
except Exception:  # pragma: no cover
    _SEMANTIC_AVAILABLE = False


_checkpointer = None
_store = None


def get_checkpointer():
    """Return the shared checkpointer instance.

    Prefers SqliteSaver (persistent) when ``SQLITE_CHECKPOINT_PATH`` is set
    and sqlite support is installed. Falls back to MemorySaver for dev.
    """
    global _checkpointer
    if _checkpointer is not None:
        return _checkpointer

    sqlite_path = os.getenv("SQLITE_CHECKPOINT_PATH")
    # AsyncSqliteSaver needs a running event loop at construction time, so we
    # only pick it when an event loop is already active (e.g. inside uvicorn's
    # startup hook). At module-import time we fall back to MemorySaver.
    if sqlite_path and _AIOSQLITE_AVAILABLE:
        try:
            import asyncio
            asyncio.get_running_loop()
        except RuntimeError:
            loop_running = False
        else:
            loop_running = True
        if loop_running:
            os.makedirs(os.path.dirname(os.path.abspath(sqlite_path)) or ".", exist_ok=True)
            import aiosqlite
            conn = aiosqlite.connect(sqlite_path, check_same_thread=False)
            _checkpointer = AsyncSqliteSaver(conn)
            return _checkpointer
    if sqlite_path and _SQLITE_AVAILABLE:
        # Sync path only — tests / scripts / Gradio.
        os.makedirs(os.path.dirname(os.path.abspath(sqlite_path)) or ".", exist_ok=True)
        import sqlite3
        conn = sqlite3.connect(sqlite_path, check_same_thread=False)
        _checkpointer = SqliteSaver(conn)
        return _checkpointer

    _checkpointer = MemorySaver()
    return _checkpointer


def get_store():
    """Return the shared long-term store.

    Prefers SemanticStore (Chroma-backed) when available AND
    ``MEMORY_BACKEND`` is not explicitly set to ``memory``. Falls back to
    InMemoryStore (prefix-scan only) otherwise. The returned object always
    satisfies the subset of the BaseStore interface used by the agents
    (put / search / get / delete).
    """
    global _store
    if _store is not None:
        return _store

    pg_url = os.getenv("POSTGRES_URL") or os.getenv("SUPABASE_DB_URL")
    backend = os.getenv(
        "MEMORY_BACKEND",
        "postgres" if pg_url else ("semantic" if _SEMANTIC_AVAILABLE else "memory"),
    )

    if backend == "postgres" and pg_url:
        try:
            from shared.postgres_store import PostgresSemanticStore
            _store = PostgresSemanticStore(conn_string=pg_url)
            return _store
        except Exception:
            # Any Postgres init error -> graceful fallback.
            pass

    if backend == "semantic" and _SEMANTIC_AVAILABLE:
        try:
            _store = SemanticStore()
            return _store
        except Exception:
            pass

    _store = InMemoryStore()
    return _store


def reset_memory_singletons() -> None:
    """Test hook — drop cached singletons so tests can swap backends."""
    global _checkpointer, _store
    _checkpointer = None
    _store = None
