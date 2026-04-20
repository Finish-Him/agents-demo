"""RAG retrieval tool — queries the math-for-ML knowledge base."""

from __future__ import annotations

from langchain_core.tools import tool

from arquimedes.rag.retrieval import format_passages, search


@tool
def search_knowledge_base(query: str, k: int = 4) -> str:
    """Search the math-for-ML textbook corpus (Strang, OpenStax, Deisenroth, etc.).

    Use whenever the learner asks for definitions, theorem statements, or
    citations from authoritative sources. Returns the top-k retrieved
    passages with source filename and page number.

    Args:
        query: Natural-language search query (the student's question or a
            refinement you crafted).
        k: Number of passages to return (default 4).
    """
    try:
        docs = search(query, k=k)
    except Exception as e:
        return f"(knowledge base unavailable: {e})"
    if not docs:
        return "(no passages matched this query in the knowledge base)"
    return format_passages(docs)


rag_tools = [search_knowledge_base]
