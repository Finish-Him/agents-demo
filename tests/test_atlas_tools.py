"""Tests for atlas/tools.py — tech stack consultant tools."""

import os
from unittest.mock import patch, MagicMock

import pytest

from atlas.tools import (
    search_github_repos,
    search_hf_spaces,
    analyze_project_structure,
    recommend_technology,
)


class TestSearchGithubRepos:
    """Test search_github_repos tool (mocked HTTP)."""

    @patch("atlas.tools.httpx.get")
    def test_finds_matching_repo(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = [
            {
                "name": "agents-demo",
                "description": "LangGraph agents demo",
                "language": "Python",
                "topics": ["langgraph", "fastapi"],
                "html_url": "https://github.com/Finish-Him/agents-demo",
                "stargazers_count": 5,
                "updated_at": "2026-04-19",
            },
            {
                "name": "other-project",
                "description": "Something else",
                "language": "JavaScript",
                "topics": [],
                "html_url": "https://github.com/Finish-Him/other-project",
                "stargazers_count": 0,
                "updated_at": "2026-01-01",
            },
        ]
        mock_get.return_value = mock_resp

        result = search_github_repos.invoke({"query": "langgraph"})
        assert "agents-demo" in result
        assert "1 repo" in result

    @patch("atlas.tools.httpx.get")
    def test_no_matches(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = [
            {"name": "my-repo", "description": "test", "language": "Python", "topics": [], "html_url": ""},
        ]
        mock_get.return_value = mock_resp

        result = search_github_repos.invoke({"query": "nonexistent_xyz"})
        assert "No repos matching" in result

    @patch("atlas.tools.httpx.get")
    def test_api_error(self, mock_get):
        import httpx
        mock_get.side_effect = httpx.HTTPError("Connection failed")

        result = search_github_repos.invoke({"query": "test"})
        assert "error" in result.lower()


class TestSearchHfSpaces:
    """Test search_hf_spaces tool (mocked HTTP)."""

    @patch("atlas.tools.httpx.get")
    def test_finds_spaces(self, mock_get):
        def side_effect(url, **kwargs):
            resp = MagicMock()
            resp.status_code = 200
            if "spaces" in url:
                resp.json.return_value = [
                    {"id": "Finish-him/agents-demo", "sdk": "gradio"},
                ]
            else:
                resp.json.return_value = []
            return resp

        mock_get.side_effect = side_effect

        result = search_hf_spaces.invoke({"query": "agents"})
        assert "agents-demo" in result
        assert "Space" in result

    @patch("atlas.tools.httpx.get")
    def test_no_results(self, mock_get):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = []
        mock_get.return_value = resp

        result = search_hf_spaces.invoke({"query": "nonexistent_xyz_123"})
        assert "No Spaces or Models" in result


class TestAnalyzeProjectStructure:
    """Test analyze_project_structure tool (mocked HTTP)."""

    @patch("atlas.tools.httpx.get")
    def test_successful_analysis(self, mock_get):
        def side_effect(url, **kwargs):
            resp = MagicMock()
            resp.status_code = 200
            resp.raise_for_status = MagicMock()
            if "/languages" in url:
                resp.json.return_value = {"Python": 15000, "TypeScript": 5000}
            elif "/readme" in url:
                resp.text = "# My Project\nThis is a test project."
            elif "/git/trees" in url:
                resp.json.return_value = {"tree": [{"path": "README.md"}, {"path": "api.py"}, {"path": "requirements.txt"}]}
            else:
                resp.json.return_value = {
                    "full_name": "Finish-Him/agents-demo",
                    "description": "LangGraph agents",
                    "default_branch": "main",
                    "stargazers_count": 5,
                    "forks_count": 0,
                    "created_at": "2026-01-01",
                    "updated_at": "2026-04-19",
                }
            return resp

        mock_get.side_effect = side_effect

        result = analyze_project_structure.invoke({"repo_name": "agents-demo"})
        assert "agents-demo" in result
        assert "Python" in result
        assert "README" in result

    @patch("atlas.tools.httpx.get")
    def test_api_error(self, mock_get):
        import httpx
        mock_get.side_effect = httpx.HTTPError("Not found")

        result = analyze_project_structure.invoke({"repo_name": "nonexistent"})
        assert "Error" in result


class TestRecommendTechnology:
    """Test recommend_technology tool."""

    def test_api_recommendation(self):
        result = recommend_technology.invoke({"requirement": "I need to build an API for my ML model"})
        assert "FastAPI" in result

    def test_frontend_recommendation(self):
        result = recommend_technology.invoke({"requirement": "I need a frontend framework"})
        assert "Next.js" in result or "React" in result

    def test_llm_recommendation(self):
        result = recommend_technology.invoke({"requirement": "I want to build an llm agent"})
        assert "LangGraph" in result

    def test_deploy_recommendation(self):
        result = recommend_technology.invoke({"requirement": "How should I deploy my project?"})
        assert "Docker" in result

    def test_database_recommendation(self):
        result = recommend_technology.invoke({"requirement": "I need a database for my app"})
        assert "PostgreSQL" in result

    def test_unknown_requirement(self):
        result = recommend_technology.invoke({"requirement": "I need quantum computing tools"})
        assert "FastAPI" in result or "general approach" in result.lower()
