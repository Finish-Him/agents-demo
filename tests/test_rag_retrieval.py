"""Tests for arquimedes/rag/retrieval.py using an isolated Chroma instance."""

import os
import pytest


@pytest.fixture
def isolated_rag(tmp_path, monkeypatch):
    """Point the RAG config to a temp dir and force a fresh vector store."""
    monkeypatch.setenv("CHROMA_PATH", str(tmp_path / "chroma"))
    monkeypatch.setenv("RAG_COLLECTION", "test_arquimedes")
    # Force pure-local embeddings (no OpenAI API needed for tests).
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    # Reload config + singletons so envvars take effect.
    import importlib
    import arquimedes.rag.config as config
    import arquimedes.rag.vector_store as vs_mod
    import arquimedes.rag.retrieval as retr
    importlib.reload(config)
    importlib.reload(vs_mod)
    importlib.reload(retr)
    vs_mod.reset_vector_store_singleton()

    from langchain_core.documents import Document
    docs = [
        Document(
            page_content="An eigenvector v of a matrix A satisfies Av = lambda v.",
            metadata={"source": "la.md", "topic": "linear_algebra"},
        ),
        Document(
            page_content="The chain rule: dy/dx = f'(g(x)) g'(x) for composed functions.",
            metadata={"source": "calc.md", "topic": "calculus"},
        ),
        Document(
            page_content="Bayes theorem: P(H|E) = P(E|H) P(H) / P(E).",
            metadata={"source": "prob.md", "topic": "probability"},
        ),
    ]
    vs = vs_mod.get_vector_store()
    vs.add_documents(docs)
    return retr


class TestSearch:
    def test_eigenvector_query_hits_la_doc(self, isolated_rag):
        results = isolated_rag.search("what is an eigenvector", k=3)
        assert len(results) > 0
        top = results[0]
        assert "eigenvector" in top.page_content.lower()
        assert top.metadata["source"] == "la.md"

    def test_bayes_query_hits_prob_doc(self, isolated_rag):
        results = isolated_rag.search("bayes theorem formula", k=3)
        assert len(results) > 0
        top = results[0]
        assert top.metadata["source"] == "prob.md"

    def test_format_passages_includes_source(self, isolated_rag):
        results = isolated_rag.search("chain rule", k=2)
        text = isolated_rag.format_passages(results)
        assert "calc.md" in text
