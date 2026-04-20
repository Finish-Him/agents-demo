"""Pydantic schemas used by Arquimedes LCEL chains.

These models drive `llm.with_structured_output(...)` calls so we get typed,
validated outputs instead of string parsing.
"""

from typing import Literal

from pydantic import BaseModel, Field


class StudentProfileFact(BaseModel):
    """A single atomic fact about the learner, suitable for semantic memory."""

    topic: str = Field(..., description="Topic touched (e.g., 'eigenvectors', 'chain rule').")
    level: Literal["beginner", "intermediate", "advanced"] = Field(
        ..., description="Learner's level on this topic based on conversation."
    )
    confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence in the level estimate (0-1)."
    )
    evidence: str = Field(
        ..., description="One-sentence justification citing what the student said or did."
    )


class StudentProfileUpdate(BaseModel):
    """Collection of facts extracted from the latest conversation slice."""

    has_new_information: bool = Field(
        ..., description="False if the last turns contained no new teaching signal."
    )
    facts: list[StudentProfileFact] = Field(
        default_factory=list, description="Atomic facts; empty when has_new_information is False."
    )


class RouterDecision(BaseModel):
    """Where to send the conversation next after the assistant produced a response."""

    route: Literal["rag", "tools", "direct"] = Field(
        ...,
        description=(
            "'rag'  -> need to look something up in the math knowledge base; "
            "'tools' -> the assistant already emitted tool_calls; "
            "'direct' -> ready to end the turn."
        ),
    )
    rationale: str = Field(..., description="One-sentence justification for the choice.")


class ExerciseSpec(BaseModel):
    """Structured exercise envelope."""

    prompt: str
    hint: str
    solution: str
    difficulty: Literal["beginner", "intermediate", "advanced"]


class MathSolutionStep(BaseModel):
    """One step of a derivation."""

    description: str
    expression: str = Field(..., description="LaTeX-formatted expression after this step.")


class MathSolution(BaseModel):
    """Structured math solution with step-by-step derivation."""

    steps: list[MathSolutionStep]
    final_answer: str = Field(..., description="LaTeX-formatted final answer.")
    method: str = Field(..., description="Short name of the technique used (e.g., 'chain rule').")
