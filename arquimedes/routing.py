"""Heuristic + LCEL routing for Arquimedes.

The router decides whether the first turn of a user request should proactively
retrieve passages from the knowledge base (``rag_retrieve`` node) before the
assistant runs, or go straight to the assistant. A cheap keyword heuristic is
used by default to avoid an extra LLM call; the LCEL structured-output chain
from ``arquimedes.chains.build_router_chain`` is available for callers who
want model-driven routing.
"""

from __future__ import annotations

from typing import Literal

from langchain_core.messages import BaseMessage


_RAG_TRIGGERS = (
    "cite",
    "citation",
    "source",
    "reference",
    "quote",
    "chapter",
    "page",
    "textbook",
    "book",
    "definition of",
    "define ",
    "theorem",
    "lemma",
    "proof",
    "strang",
    "deisenroth",
    "openstax",
    "according to",
    "where in",
    "what does the book say",
)


def last_human_content(messages: list[BaseMessage]) -> str:
    for m in reversed(messages):
        if getattr(m, "type", None) == "human":
            return (getattr(m, "content", "") or "").lower()
    return ""


def should_retrieve(messages: list[BaseMessage]) -> bool:
    """Return True when the latest user turn looks citation-seeking."""
    text = last_human_content(messages)
    if not text:
        return False
    return any(trigger in text for trigger in _RAG_TRIGGERS)


def entry_route(state) -> Literal["rag_retrieve", "assistant"]:
    """Entry-edge router used by the graph."""
    if should_retrieve(state.get("messages", [])):
        return "rag_retrieve"
    return "assistant"
