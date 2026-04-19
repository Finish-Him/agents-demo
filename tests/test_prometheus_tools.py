"""Tests for prometheus/tools.py — AI governance tools."""

import pytest

from prometheus.tools import (
    lookup_regulation,
    check_penalty,
    assess_ai_risk_level,
    generate_compliance_checklist,
    calculate_deadline,
)


class TestLookupRegulation:
    """Test lookup_regulation tool."""

    def test_lookup_gdpr(self):
        result = lookup_regulation.invoke({"regulation": "GDPR"})
        assert "General Data Protection Regulation" in result
        assert "European Union" in result

    def test_lookup_gdpr_specific_article(self):
        result = lookup_regulation.invoke({"regulation": "GDPR", "article": "Art. 5"})
        assert "lawfulness" in result.lower() or "Art. 5" in result

    def test_lookup_ccpa(self):
        result = lookup_regulation.invoke({"regulation": "CCPA"})
        assert "California" in result

    def test_lookup_eu_ai_act(self):
        result = lookup_regulation.invoke({"regulation": "EU_AI_ACT"})
        assert "Artificial Intelligence Act" in result

    def test_lookup_nist(self):
        result = lookup_regulation.invoke({"regulation": "NIST_AI_RMF"})
        assert "NIST" in result

    def test_lookup_invalid_regulation(self):
        result = lookup_regulation.invoke({"regulation": "INVALID"})
        assert "not found" in result.lower()

    def test_lookup_invalid_article(self):
        result = lookup_regulation.invoke({"regulation": "GDPR", "article": "Art. 999"})
        assert "not found" in result.lower()


class TestCheckPenalty:
    """Test check_penalty tool."""

    def test_gdpr_penalties(self):
        result = check_penalty.invoke({"regulation": "GDPR"})
        assert "EUR" in result
        assert "20M" in result or "4%" in result

    def test_ccpa_penalties(self):
        result = check_penalty.invoke({"regulation": "CCPA"})
        assert "$2,500" in result or "$7,500" in result

    def test_eu_ai_act_penalties(self):
        result = check_penalty.invoke({"regulation": "EU_AI_ACT"})
        assert "35M" in result or "7%" in result

    def test_penalty_with_filter(self):
        result = check_penalty.invoke({"regulation": "GDPR", "violation_type": "upper"})
        assert "Upper" in result

    def test_penalty_invalid_regulation(self):
        result = check_penalty.invoke({"regulation": "INVALID"})
        assert "No penalty data" in result


class TestAssessAIRisk:
    """Test assess_ai_risk_level tool."""

    def test_unacceptable_risk(self):
        result = assess_ai_risk_level.invoke({"system_description": "Social scoring system for government"})
        assert "UNACCEPTABLE" in result

    def test_high_risk(self):
        result = assess_ai_risk_level.invoke({"system_description": "AI system for hiring and recruitment screening"})
        assert "HIGH" in result

    def test_limited_risk(self):
        result = assess_ai_risk_level.invoke({"system_description": "Customer service chatbot"})
        assert "LIMITED" in result

    def test_minimal_risk(self):
        result = assess_ai_risk_level.invoke({"system_description": "AI-powered spam filter for emails"})
        assert "MINIMAL" in result


class TestGenerateChecklist:
    """Test generate_compliance_checklist tool."""

    def test_gdpr_general(self):
        result = generate_compliance_checklist.invoke({"regulation": "GDPR", "processing_type": "general"})
        assert "Checklist" in result
        assert "Art. 6" in result or "lawful basis" in result.lower()

    def test_gdpr_ai_system(self):
        result = generate_compliance_checklist.invoke({"regulation": "GDPR", "processing_type": "ai_system"})
        assert "DPIA" in result or "automated" in result.lower()

    def test_eu_ai_act_checklist(self):
        result = generate_compliance_checklist.invoke({"regulation": "EU_AI_ACT", "processing_type": "ai_system"})
        assert "risk" in result.lower()

    def test_ccpa_general(self):
        result = generate_compliance_checklist.invoke({"regulation": "CCPA", "processing_type": "general"})
        assert "privacy" in result.lower() or "consumer" in result.lower()

    def test_invalid_combination(self):
        result = generate_compliance_checklist.invoke({"regulation": "GDPR", "processing_type": "unknown_type"})
        assert "No checklist" in result or "Available" in result


class TestCalculateDeadline:
    """Test calculate_deadline tool."""

    def test_gdpr_breach(self):
        result = calculate_deadline.invoke({"event_type": "gdpr_breach_notify", "event_date": "2026-04-19"})
        assert "72 hours" in result or "3 days" in result.lower() or "Deadline: 3" in result

    def test_ccpa_request(self):
        result = calculate_deadline.invoke({"event_type": "ccpa_request", "event_date": "2026-04-19"})
        assert "45" in result

    def test_invalid_event_type(self):
        result = calculate_deadline.invoke({"event_type": "invalid_event", "event_date": "2026-04-19"})
        assert "Unknown" in result or "Available" in result

    def test_invalid_date_format(self):
        result = calculate_deadline.invoke({"event_type": "gdpr_breach_notify", "event_date": "not-a-date"})
        assert "Invalid date" in result
