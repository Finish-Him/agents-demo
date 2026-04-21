"""Hybrid retrieval (BM25 + dense) with optional cross-encoder rerank."""

from __future__ import annotations

from typing import Iterable

from langchain_core.documents import Document

from arquimedes.rag.config import DEFAULT_K, ENABLE_RERANK, RERANK_MODEL
from arquimedes.rag.vector_store import get_vector_store


def _dense_retrieve(query: str, k: int) -> list[Document]:
    vs = get_vector_store()
    return vs.similarity_search(query, k=k)


def _bm25_retrieve(query: str, k: int) -> list[Document]:
    """BM25 over whatever is currently in Chroma. Lazy-rebuilt per call.

    For production scale this should be cached or swapped for a proper
    inverted index. For a demo corpus (hundreds of docs) it's fine.
    """
    vs = get_vector_store()
    try:
        all_docs_raw = vs.get()
    except Exception:
        return []
    docs = all_docs_raw.get("documents", []) or []
    metas = all_docs_raw.get("metadatas", []) or []
    if not docs:
        return []

    from langchain_community.retrievers import BM25Retriever

    documents = [Document(page_content=d, metadata=m or {}) for d, m in zip(docs, metas)]
    retriever = BM25Retriever.from_documents(documents)
    retriever.k = k
    return retriever.invoke(query)


def _hybrid_merge(dense: list[Document], sparse: list[Document], k: int) -> list[Document]:
    """Reciprocal Rank Fusion of two ranked lists."""
    scores: dict[str, float] = {}
    ordering: dict[str, Document] = {}
    C = 60.0  # standard RRF constant
    for rank, doc in enumerate(dense):
        key = doc.page_content
        scores[key] = scores.get(key, 0.0) + 1.0 / (C + rank)
        ordering.setdefault(key, doc)
    for rank, doc in enumerate(sparse):
        key = doc.page_content
        scores[key] = scores.get(key, 0.0) + 1.0 / (C + rank)
        ordering.setdefault(key, doc)
    ranked = sorted(scores.items(), key=lambda kv: -kv[1])
    return [ordering[key] for key, _ in ranked[:k]]


def _maybe_rerank(query: str, docs: list[Document]) -> list[Document]:
    if not ENABLE_RERANK or not docs:
        return docs
    try:
        from sentence_transformers import CrossEncoder

        model = CrossEncoder(RERANK_MODEL)
        pairs = [(query, d.page_content) for d in docs]
        scores = model.predict(pairs)
        return [d for _, d in sorted(zip(scores, docs), key=lambda s: -s[0])]
    except Exception:
        return docs


def search(query: str, k: int = DEFAULT_K) -> list[Document]:
    """Hybrid BM25 + dense retrieval, with optional cross-encoder rerank."""
    dense = _dense_retrieve(query, k=max(k, 4))
    sparse = _bm25_retrieve(query, k=max(k, 4))
    merged = _hybrid_merge(dense, sparse, k=k)
    return _maybe_rerank(query, merged)


def format_passages(docs: Iterable[Document]) -> str:
    """Render retrieved passages with source citations for the LLM."""
    out_lines: list[str] = []
    for i, d in enumerate(docs, 1):
        src = d.metadata.get("source", "unknown")
        page = d.metadata.get("page")
        header = f"[{i}] {src}" + (f" (p.{page})" if page is not None else "")
        out_lines.append(f"{header}\n{d.page_content.strip()}")
    return "\n\n".join(out_lines)
