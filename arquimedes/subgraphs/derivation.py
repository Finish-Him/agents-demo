"""Derivation subgraph: plan → step → verify loop for multi-step proofs.

Demonstrates LangGraph subgraph composition: the assistant can invoke
``step_by_step_derive(problem)`` as a tool; internally it compiles a small
StateGraph of its own that plans a proof outline, fills in each step, and
verifies the final answer. Every step is logged in the returned text so the
learner sees the structure.
"""

from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from shared.llm import get_llm


class DerivationState(TypedDict, total=False):
    problem: str
    plan: list[str]
    steps: list[str]
    final_answer: str
    verified: bool


def _plan_node(state: DerivationState) -> DerivationState:
    llm = get_llm()
    prompt = (
        "You are a math teacher planning a short proof. "
        "Given the problem, emit a numbered list (3–6 items) of high-level "
        "steps to solve it. Do not solve yet — only outline."
    )
    resp = llm.invoke(
        [SystemMessage(content=prompt), HumanMessage(content=state["problem"])]
    )
    lines = [ln.strip(" -0123456789.") for ln in resp.content.splitlines() if ln.strip()]
    return {"plan": lines[:8]}


def _step_node(state: DerivationState) -> DerivationState:
    llm = get_llm()
    plan_text = "\n".join(f"- {p}" for p in state.get("plan", []))
    prompt = (
        "Execute the plan step by step. For each item in the plan, write one "
        "short paragraph with the algebraic manipulation or formal argument. "
        "Use LaTeX for formulas ($...$). End with a line starting with "
        "'Final answer:' followed by the conclusion."
    )
    resp = llm.invoke(
        [
            SystemMessage(content=prompt),
            HumanMessage(content=f"Problem: {state['problem']}\n\nPlan:\n{plan_text}"),
        ]
    )
    text = resp.content
    steps = [s.strip() for s in text.split("\n\n") if s.strip()]
    final_answer = ""
    for line in text.splitlines():
        if line.lower().startswith("final answer"):
            final_answer = line.split(":", 1)[-1].strip()
            break
    return {"steps": steps, "final_answer": final_answer or text.strip()}


def _verify_node(state: DerivationState) -> DerivationState:
    llm = get_llm()
    prompt = (
        "You are a strict proof-checker. Given the problem and the proposed "
        "derivation below, answer with a single word: 'VERIFIED' if the logic "
        "is sound and the final answer correct, or 'FLAWED: <short reason>' "
        "otherwise."
    )
    derivation = "\n\n".join(state.get("steps", []))
    resp = llm.invoke(
        [
            SystemMessage(content=prompt),
            HumanMessage(
                content=f"Problem: {state['problem']}\n\nDerivation:\n{derivation}"
            ),
        ]
    )
    verified = resp.content.strip().upper().startswith("VERIFIED")
    return {"verified": verified}


def build_derivation_subgraph():
    builder = StateGraph(DerivationState)
    builder.add_node("plan", _plan_node)
    builder.add_node("step", _step_node)
    builder.add_node("verify", _verify_node)
    builder.add_edge(START, "plan")
    builder.add_edge("plan", "step")
    builder.add_edge("step", "verify")
    builder.add_edge("verify", END)
    return builder.compile()


_derivation_graph = None


def solve_derivation(problem: str) -> str:
    """Run the subgraph and format a human-readable trace."""
    global _derivation_graph
    if _derivation_graph is None:
        _derivation_graph = build_derivation_subgraph()
    state = _derivation_graph.invoke({"problem": problem})
    lines: list[str] = []
    lines.append("DERIVATION")
    lines.append(f"Problem: {problem}")
    if state.get("plan"):
        lines.append("\nPlan:")
        for i, p in enumerate(state["plan"], 1):
            lines.append(f"  {i}. {p}")
    if state.get("steps"):
        lines.append("\nSteps:")
        for s in state["steps"]:
            lines.append(s)
    lines.append(
        f"\nFinal answer: {state.get('final_answer', '(none)')}"
    )
    lines.append(
        f"Verifier: {'VERIFIED' if state.get('verified') else 'REVIEW NEEDED'}"
    )
    return "\n".join(lines)
