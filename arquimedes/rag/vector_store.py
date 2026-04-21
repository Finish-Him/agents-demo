"""Singleton Chroma vector store wired to the Arquimedes embedding factory."""

from __future__ import annotations

import os

from arquimedes.rag.config import CHROMA_PATH, COLLECTION
from arquimedes.rag.embeddings import get_embeddings


_vector_store = None


def get_vector_store():
    """Return a process-wide singleton Chroma instance."""
    global _vector_store
    if _vector_store is not None:
        return _vector_store

    os.makedirs(CHROMA_PATH, exist_ok=True)

    from langchain_chroma import Chroma

    _vector_store = Chroma(
        collection_name=COLLECTION,
        embedding_function=get_embeddings(),
        persist_directory=CHROMA_PATH,
    )
    return _vector_store


def reset_vector_store_singleton() -> None:
    """Test hook."""
    global _vector_store
    _vector_store = None
