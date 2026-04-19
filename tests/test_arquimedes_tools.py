"""Tests for arquimedes/tools.py — adaptive teaching tools."""

import pytest

from arquimedes.tools import (
    assess_level,
    generate_exercise,
    explain_concept,
    find_resources,
)


class TestAssessLevel:
    """Test assess_level tool."""

    def test_beginner_level(self):
        result = assess_level.invoke({
            "subject": "python",
            "student_response": "I'm just starting to learn coding",
        })
        assert "BEGINNER" in result

    def test_intermediate_level(self):
        result = assess_level.invoke({
            "subject": "machine_learning",
            "student_response": "I know about cross-validation and feature engineering",
        })
        assert "INTERMEDIATE" in result

    def test_advanced_level(self):
        result = assess_level.invoke({
            "subject": "deep_learning",
            "student_response": "I've implemented transformer models with attention mechanisms",
        })
        assert "ADVANCED" in result

    def test_invalid_subject(self):
        result = assess_level.invoke({
            "subject": "cooking",
            "student_response": "I know how to boil water",
        })
        assert "not available" in result.lower()

    def test_llm_agents_subject(self):
        result = assess_level.invoke({
            "subject": "llm_agents",
            "student_response": "I've used langgraph for multi-agent systems",
        })
        assert "ADVANCED" in result

    def test_includes_topic_recommendations(self):
        result = assess_level.invoke({
            "subject": "python",
            "student_response": "I know variables and loops",
        })
        assert "topics" in result.lower() or "Recommended" in result


class TestGenerateExercise:
    """Test generate_exercise tool."""

    def test_python_beginner(self):
        result = generate_exercise.invoke({
            "subject": "python",
            "topic": "Variables",
            "level": "beginner",
        })
        assert "EXERCISE" in result
        assert "variable" in result.lower() or "name" in result.lower()

    def test_python_intermediate(self):
        result = generate_exercise.invoke({
            "subject": "python",
            "topic": "List Comprehensions",
            "level": "intermediate",
        })
        assert "EXERCISE" in result
        assert "comprehension" in result.lower() or "list" in result.lower()

    def test_python_advanced(self):
        result = generate_exercise.invoke({
            "subject": "python",
            "topic": "Decorators",
            "level": "advanced",
        })
        assert "EXERCISE" in result
        assert "decorator" in result.lower() or "timer" in result.lower()

    def test_ml_beginner(self):
        result = generate_exercise.invoke({
            "subject": "machine_learning",
            "topic": "Types of ML",
            "level": "beginner",
        })
        assert "EXERCISE" in result

    def test_deep_learning_advanced(self):
        result = generate_exercise.invoke({
            "subject": "deep_learning",
            "topic": "Attention",
            "level": "advanced",
        })
        assert "EXERCISE" in result
        assert "attention" in result.lower() or "transformer" in result.lower()

    def test_fallback_exercise(self):
        result = generate_exercise.invoke({
            "subject": "unknown_subject",
            "topic": "Something",
            "level": "beginner",
        })
        assert "EXERCISE" in result


class TestExplainConcept:
    """Test explain_concept tool."""

    def test_neural_network_with_analogy(self):
        result = explain_concept.invoke({
            "concept": "neural network",
            "level": "beginner",
            "use_analogy": True,
        })
        assert "Analogy" in result
        assert "team" in result.lower() or "decision" in result.lower()

    def test_gradient_descent_analogy(self):
        result = explain_concept.invoke({
            "concept": "gradient descent",
            "level": "intermediate",
            "use_analogy": True,
        })
        assert "Analogy" in result
        assert "hiker" in result.lower() or "blindfolded" in result.lower()

    def test_without_analogy(self):
        result = explain_concept.invoke({
            "concept": "overfitting",
            "level": "advanced",
            "use_analogy": False,
        })
        assert "EXPLANATION" in result
        assert "Analogy" not in result

    def test_unknown_concept_analogy_fallback(self):
        result = explain_concept.invoke({
            "concept": "quantum computing",
            "level": "beginner",
            "use_analogy": True,
        })
        assert "no specific analogy" in result.lower() or "Analogy" in result

    def test_rag_analogy(self):
        result = explain_concept.invoke({
            "concept": "RAG retrieval augmented generation",
            "level": "intermediate",
            "use_analogy": True,
        })
        assert "open-book" in result.lower() or "exam" in result.lower()


class TestFindResources:
    """Test find_resources tool."""

    def test_python_resources(self):
        result = find_resources.invoke({"topic": "python programming"})
        assert "Python" in result
        assert "http" in result.lower()

    def test_ml_resources(self):
        result = find_resources.invoke({"topic": "machine_learning"})
        assert "Andrew Ng" in result or "Coursera" in result or "Machine" in result

    def test_deep_learning_resources(self):
        result = find_resources.invoke({"topic": "deep_learning"})
        assert "fast.ai" in result or "Deep Learning" in result

    def test_llm_resources(self):
        result = find_resources.invoke({"topic": "llm agents"})
        assert "LangChain" in result or "LangGraph" in result

    def test_transformer_resources(self):
        result = find_resources.invoke({"topic": "transformer architecture"})
        assert "Attention" in result or "HuggingFace" in result

    def test_unknown_topic_fallback(self):
        result = find_resources.invoke({"topic": "quantum mechanics"})
        assert "General suggestions" in result or "YouTube" in result
