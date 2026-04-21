"""Semantic student-profile store backed by ChromaDB.

Implements the tiny subset of the LangGraph BaseStore surface that the
Arquimedes agent needs: `put`, `search`, `get`, `delete`. Unlike
`InMemoryStore.search(namespace)` (prefix scan), this `search` does
similarity retrieval when a `query` string is provided — so we inject only
the facts relevant to the current user turn into the system prompt.

Designed to be swappable for pgvector on Supabase in production: same
public interface; backend is selected via env var.
"""

from __future__ import annotations

import os
from typing import Any, Iterable

from shared.store_types import StoreRecord, namespace_key as _ns

try:  # pragma: no cover - import guard
    import chromadb
    from chromadb.config import Settings
    _CHROMA_AVAILABLE = True
except Exception:  # pragma: no cover
    _CHROMA_AVAILABLE = False


class SemanticStore:
    """Chroma-backed store with BaseStore-compatible surface (subset)."""

    def __init__(
        self,
        persist_directory: str | None = None,
        collection_name: str = "arquimedes_memory",
        embedding_function=None,
    ):
        if not _CHROMA_AVAILABLE:
            raise RuntimeError(
                "chromadb is not installed. `pip install chromadb` or fall back "
                "to get_store(semantic=False)."
            )
        persist_directory = persist_directory or os.getenv(
            "MEMORY_CHROMA_PATH", "./data/memory_chroma"
        )
        os.makedirs(persist_directory, exist_ok=True)
        self._client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False),
        )
        # Use ChromaDB's default embedding function (MiniLM via onnxruntime)
        # unless caller injected a specific one. This avoids a hard OpenAI key
        # requirement for memory to work.
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            embedding_function=embedding_function,
        )

    # ── BaseStore-compatible API ──────────────────────────────────────────
    def put(self, namespace: tuple[str, ...], key: str, value: dict[str, Any]) -> None:
        doc = value.get("content") or str(value)
        metadata = {k: v for k, v in value.items() if k != "content"}
        metadata["namespace"] = _ns(namespace)
        metadata["key"] = key
        # Chroma requires scalar metadata values
        metadata = {k: v for k, v in metadata.items() if isinstance(v, (str, int, float, bool))}
        self._collection.upsert(
            ids=[f"{_ns(namespace)}::{key}"],
            documents=[doc],
            metadatas=[metadata],
        )

    def search(
        self,
        namespace: tuple[str, ...],
        query: str | None = None,
        limit: int = 5,
    ) -> list[StoreRecord]:
        ns_filter = {"namespace": _ns(namespace)}
        if query:
            res = self._collection.query(
                query_texts=[query],
                n_results=limit,
                where=ns_filter,
            )
            docs = (res.get("documents") or [[]])[0]
            metas = (res.get("metadatas") or [[]])[0]
            ids = (res.get("ids") or [[]])[0]
        else:
            res = self._collection.get(where=ns_filter, limit=limit)
            docs = res.get("documents") or []
            metas = res.get("metadatas") or []
            ids = res.get("ids") or []

        out: list[StoreRecord] = []
        for _id, doc, meta in zip(ids, docs, metas):
            value = {"content": doc}
            if meta:
                value.update({k: v for k, v in meta.items() if k not in ("namespace",)})
            out.append(StoreRecord(namespace=namespace, key=meta.get("key", _id), value=value))
        return out

    def get(self, namespace: tuple[str, ...], key: str) -> StoreRecord | None:
        res = self._collection.get(ids=[f"{_ns(namespace)}::{key}"])
        docs = res.get("documents") or []
        if not docs:
            return None
        meta = (res.get("metadatas") or [{}])[0]
        value = {"content": docs[0]}
        if meta:
            value.update({k: v for k, v in meta.items() if k != "namespace"})
        return StoreRecord(namespace=namespace, key=key, value=value)

    def delete(self, namespace: tuple[str, ...], key: str) -> None:
        self._collection.delete(ids=[f"{_ns(namespace)}::{key}"])

    def list_namespaces(self, prefix: Iterable[str] | None = None) -> list[tuple[str, ...]]:
        # Minimal implementation: return all distinct namespaces seen so far.
        all_meta = self._collection.get(include=["metadatas"]).get("metadatas", [])
        seen = set()
        for m in all_meta:
            ns = m.get("namespace")
            if ns:
                seen.add(tuple(ns.split("::")))
        return sorted(seen)
