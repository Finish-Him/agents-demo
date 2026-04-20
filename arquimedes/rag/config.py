"""Configuration for the Arquimedes RAG pipeline."""

from __future__ import annotations

import os

CHROMA_PATH = os.getenv("CHROMA_PATH", "./data/chroma")
COLLECTION = os.getenv("RAG_COLLECTION", "arquimedes_math")

# Embedding model: OpenAI if key available, else local MiniLM.
OPENAI_EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
HF_EMBED_MODEL = os.getenv(
    "HF_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
)

# Retrieval knobs
DEFAULT_K = int(os.getenv("RAG_K", "4"))
ENABLE_RERANK = os.getenv("RAG_RERANK", "false").lower() == "true"
RERANK_MODEL = os.getenv(
    "RERANK_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2"
)

# Chunking
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "120"))
