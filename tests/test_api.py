"""Integration tests for the FastAPI API endpoints."""

import os
from unittest.mock import patch, AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a TestClient for the FastAPI app."""
    # Import here so env vars are set before module load
    from api import app
    return TestClient(app)


class TestHealthEndpoint:
    """Test GET /health."""

    def test_health_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "agents" in data
        assert isinstance(data["agents"], list)
        assert len(data["agents"]) == 3

    def test_health_has_all_agents(self, client):
        resp = client.get("/health")
        agents = resp.json()["agents"]
        assert "prometheus" in agents
        assert "arquimedes" in agents
        assert "atlas" in agents


class TestAgentsEndpoint:
    """Test GET /agents."""

    def test_list_agents(self, client):
        resp = client.get("/agents")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3

    def test_agent_has_required_fields(self, client):
        resp = client.get("/agents")
        data = resp.json()
        for agent_key in ["prometheus", "arquimedes", "atlas"]:
            agent = data[agent_key]
            assert "name" in agent
            assert "description" in agent
            assert "lang" in agent
            assert "examples" in agent
            assert isinstance(agent["examples"], list)
            assert len(agent["examples"]) > 0

    def test_prometheus_agent_info(self, client):
        resp = client.get("/agents")
        prometheus = resp.json()["prometheus"]
        assert prometheus["name"] == "Prometheus"
        desc = prometheus["description"].lower()
        # Accept either EN or PT phrasing — copy may be localised.
        assert any(
            kw in desc
            for kw in ("governance", "governança", "privacy", "privacidade", "compliance", "gdpr")
        )


class TestModelsEndpoint:
    """Test GET /models."""

    def test_list_models(self, client):
        resp = client.get("/models")
        assert resp.status_code == 200
        data = resp.json()
        assert "default" in data
        assert "available" in data
        assert isinstance(data["available"], list)
        assert len(data["available"]) >= 4

    def test_models_have_required_fields(self, client):
        resp = client.get("/models")
        for model in resp.json()["available"]:
            assert "id" in model
            assert "name" in model
            assert "speed" in model

    def test_qwen3_in_models(self, client):
        resp = client.get("/models")
        model_ids = [m["id"] for m in resp.json()["available"]]
        assert "qwen/qwen3-235b-a22b" in model_ids


class TestChatEndpoint:
    """Test POST /chat/{agent_name}."""

    def test_invalid_agent_404(self, client):
        resp = client.post("/chat/nonexistent", json={"message": "hello"})
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

    def test_stream_invalid_agent_404(self, client):
        resp = client.post("/chat/nonexistent/stream", json={"message": "hello"})
        assert resp.status_code == 404


class TestOpenAPIDocs:
    """Test that OpenAPI docs are accessible (not shadowed by SPA)."""

    def test_openapi_json(self, client):
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        data = resp.json()
        assert "openapi" in data
        assert "paths" in data
