"""Embedding factory with OpenAI -> HuggingFace graceful fallback."""

from __future__ import annotations

import os

from arquimedes.rag.config import HF_EMBED_MODEL, OPENAI_EMBED_MODEL


def get_embeddings():
    """Return a LangChain Embeddings instance.

    Prefers OpenAI ``text-embedding-3-small`` when ``OPENAI_API_KEY`` is
    set (best retrieval quality per dollar, 1536 dims). Falls back to
    ``sentence-transformers/all-MiniLM-L6-v2`` running locally (free,
    384 dims) so the demo works offline.
    """
    if os.getenv("OPENAI_API_KEY"):
        try:
            from langchain_openai import OpenAIEmbeddings
            return OpenAIEmbeddings(model=OPENAI_EMBED_MODEL)
        except Exception:
            pass

    from langchain_huggingface import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(model_name=HF_EMBED_MODEL)
