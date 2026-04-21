"""Tool wrapper for the derivation subgraph."""

from __future__ import annotations

from langchain_core.tools import tool

from arquimedes.subgraphs.derivation import solve_derivation


@tool
def step_by_step_derive(problem: str) -> str:
    """Solve a math problem with a planner → step → verifier subgraph.

    Use for non-trivial derivations (proofs, gradients, multi-step
    integrals) where you want the student to see the full structured
    reasoning. Returns the plan, each step, the final answer, and a
    verifier verdict.

    Args:
        problem: The math problem, stated as a sentence. LaTeX is OK.
    """
    try:
        return solve_derivation(problem)
    except Exception as e:
        return f"(derivation failed: {e})"


derivation_tools = [step_by_step_derive]
