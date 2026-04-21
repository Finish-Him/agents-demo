"""Shared types for long-term memory backends.

Both ``shared.semantic_store.SemanticStore`` (Chroma-backed) and
``shared.postgres_store.PostgresSemanticStore`` (pgvector-backed)
implement the same minimal subset of the LangGraph BaseStore surface
(``put`` / ``search`` / ``get`` / ``delete``). They return identically
shaped records, defined here once so the two backends stay in lock-step.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class StoreRecord:
    """Lightweight object compatible with langgraph.store.base.Item."""

    namespace: tuple[str, ...]
    key: str
    value: dict[str, Any]


def namespace_key(namespace: tuple[str, ...] | list[str]) -> str:
    """Encode a namespace tuple as a single string for storage backends
    that key by string only.
    """
    return "::".join(namespace)
