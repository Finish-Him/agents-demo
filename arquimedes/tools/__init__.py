"""Arquimedes tools package.

Aggregates teaching, RAG retrieval, and (future) symbolic / plotting /
fine-tuned-solver tools. Every new tool module appends to ``all_tools``
so both the LangGraph agent and the MCP server pick them up automatically.
"""

from arquimedes.tools.rag_tool import rag_tools, search_knowledge_base
from arquimedes.tools.teaching import (
    assess_level,
    explain_concept,
    find_resources,
    generate_exercise,
    teaching_tools,
)

__all__ = [
    "assess_level",
    "explain_concept",
    "find_resources",
    "generate_exercise",
    "search_knowledge_base",
    "teaching_tools",
    "rag_tools",
    "all_tools",
]

# Central registry — every new tool module appends here.
all_tools = list(teaching_tools) + list(rag_tools)
