"""Tests for arquimedes/rag/chunking.py — LaTeX-aware + hierarchical splitters."""

from arquimedes.rag.chunking import (
    chunk_documents,
    hierarchical_chunk,
    latex_aware_split,
)
from langchain_core.documents import Document


class TestLatexAwareSplit:
    def test_inline_formula_not_split(self):
        text = "The chain rule states that $\\frac{dy}{dx} = f'(g(x)) g'(x)$ for composed functions."
        chunks = latex_aware_split(text)
        assert len(chunks) >= 1
        full = " ".join(c.page_content for c in chunks)
        assert "$\\frac{dy}{dx} = f'(g(x)) g'(x)$" in full

    def test_display_formula_preserved(self):
        text = (
            "Consider the MSE loss. $$L(w) = \\frac{1}{n} \\sum_i (y_i - w^T x_i)^2$$ "
            "Its gradient is computed by linearity of differentiation."
        )
        chunks = latex_aware_split(text)
        assert any("$$L(w)" in c.page_content for c in chunks)

    def test_metadata_propagates(self):
        text = "Some prose. $x^2$ More prose."
        chunks = latex_aware_split(text, metadata={"source": "foo.md", "topic": "calculus"})
        assert all(c.metadata["source"] == "foo.md" for c in chunks)
        assert all(c.metadata["topic"] == "calculus" for c in chunks)


class TestHierarchicalChunk:
    def test_parent_child_relationship(self):
        long_text = ("Paragraph about eigenvectors. " * 200)
        res = hierarchical_chunk(long_text)
        assert len(res.parents) >= 1
        assert len(res.children) >= len(res.parents)
        parent_ids = {p.metadata["parent_id"] for p in res.parents}
        child_parents = {c.metadata["parent_id"] for c in res.children}
        assert child_parents.issubset(parent_ids)

    def test_chunk_types_tagged(self):
        res = hierarchical_chunk("hello world " * 500)
        assert all(p.metadata["chunk_type"] == "parent" for p in res.parents)
        assert all(c.metadata["chunk_type"] == "child" for c in res.children)


class TestChunkDocuments:
    def test_latex_aware_strategy(self):
        docs = [
            Document(page_content="Prose. $x^2 + y^2$ more prose.", metadata={"source": "a.md"})
        ]
        chunks = chunk_documents(docs, strategy="latex_aware")
        assert len(chunks) >= 1
        assert all(c.metadata["source"] == "a.md" for c in chunks)
