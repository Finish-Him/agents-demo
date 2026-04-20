"""Arquimedes tools package.

Aggregates teaching tools (current phase). Future phases will add:
- symbolic.py      (SymPy)
- plotting.py      (matplotlib)
- rag_tool.py      (ChromaDB retrieval)
- finetuned_solver.py (HF LoRA adapter)
- derivation.py    (subgraph wrapper)
"""

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
    "teaching_tools",
    "all_tools",
]

# Central registry — every new tool module appends here.
all_tools = list(teaching_tools)
