"""Domain tools for the Atlas stack specialist agent."""

import os

import httpx
from langchain_core.tools import tool

GITHUB_USER = "Finish-Him"
HF_USER = "Finish-him"


def _github_headers() -> dict:
    token = os.getenv("GITHUB_TOKEN", "")
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _hf_headers() -> dict:
    token = os.getenv("HF_TOKEN", "")
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


@tool
def search_github_repos(query: str) -> str:
    """Search the user's GitHub repositories by keyword.

    Args:
        query: Search keyword (e.g. 'langraph', 'fastapi', 'next.js').
    """
    url = f"https://api.github.com/users/{GITHUB_USER}/repos"
    params = {"per_page": 100, "sort": "updated"}
    try:
        resp = httpx.get(url, headers=_github_headers(), params=params, timeout=15)
        resp.raise_for_status()
        repos = resp.json()
    except httpx.HTTPError as e:
        return f"GitHub API error: {e}"

    query_lower = query.lower()
    matches = []
    for r in repos:
        name = (r.get("name") or "").lower()
        desc = (r.get("description") or "").lower()
        lang = (r.get("language") or "").lower()
        topics = " ".join(r.get("topics") or []).lower()
        searchable = f"{name} {desc} {lang} {topics}"
        if query_lower in searchable:
            matches.append(r)

    if not matches:
        all_names = [r["name"] for r in repos[:20]]
        return (
            f"No repos matching '{query}'. "
            f"Available repos (first 20): {', '.join(all_names)}"
        )

    result = f"Found {len(matches)} repo(s) matching '{query}':\n\n"
    for r in matches[:5]:
        result += (
            f"  📦 {r['name']}\n"
            f"     Description: {r.get('description') or 'N/A'}\n"
            f"     Language: {r.get('language') or 'N/A'}\n"
            f"     Stars: {r.get('stargazers_count', 0)}\n"
            f"     URL: {r['html_url']}\n"
            f"     Updated: {r.get('updated_at', 'N/A')}\n\n"
        )
    return result


@tool
def search_hf_spaces(query: str) -> str:
    """Search the user's Hugging Face Spaces and models.

    Args:
        query: Search keyword (e.g. 'tts', 'chatbot', 'summarizer').
    """
    # Search Spaces
    spaces_url = f"https://huggingface.co/api/spaces?author={HF_USER}"
    models_url = f"https://huggingface.co/api/models?author={HF_USER}"

    results = []
    try:
        resp = httpx.get(spaces_url, headers=_hf_headers(), timeout=15)
        if resp.status_code == 200:
            spaces = resp.json()
            query_lower = query.lower()
            for s in spaces:
                sid = (s.get("id") or "").lower()
                if query_lower in sid or not query.strip():
                    results.append(
                        f"  🚀 Space: {s.get('id')}\n"
                        f"     SDK: {s.get('sdk', 'N/A')}\n"
                        f"     URL: https://huggingface.co/spaces/{s.get('id')}\n"
                    )
    except httpx.HTTPError:
        results.append("  (Could not fetch Spaces)")

    try:
        resp = httpx.get(models_url, headers=_hf_headers(), timeout=15)
        if resp.status_code == 200:
            models = resp.json()
            query_lower = query.lower()
            for m in models:
                mid = (m.get("id") or "").lower()
                if query_lower in mid or not query.strip():
                    results.append(
                        f"  🤖 Model: {m.get('id')}\n"
                        f"     Pipeline: {m.get('pipeline_tag', 'N/A')}\n"
                        f"     URL: https://huggingface.co/models/{m.get('id')}\n"
                    )
    except httpx.HTTPError:
        results.append("  (Could not fetch Models)")

    if not results:
        return f"No Spaces or Models matching '{query}' found for user {HF_USER}."

    return f"HuggingFace resources for '{query}':\n\n" + "\n".join(results)


@tool
def analyze_project_structure(repo_name: str) -> str:
    """Analyze the structure of a GitHub repository (README, languages, dependencies).

    Args:
        repo_name: Repository name (e.g. 'youtube_summarizer').
    """
    base_url = f"https://api.github.com/repos/{GITHUB_USER}/{repo_name}"
    headers = _github_headers()

    try:
        # Get repo info
        resp = httpx.get(base_url, headers=headers, timeout=15)
        resp.raise_for_status()
        repo = resp.json()

        # Get languages
        lang_resp = httpx.get(f"{base_url}/languages", headers=headers, timeout=15)
        languages = lang_resp.json() if lang_resp.status_code == 200 else {}

        # Get README
        readme_resp = httpx.get(
            f"{base_url}/readme",
            headers={**headers, "Accept": "application/vnd.github.v3.raw"},
            timeout=15,
        )
        readme = readme_resp.text[:1500] if readme_resp.status_code == 200 else "No README found"

        # Get root tree for file listing
        tree_resp = httpx.get(
            f"{base_url}/git/trees/{repo.get('default_branch', 'main')}",
            headers=headers,
            timeout=15,
        )
        files = []
        if tree_resp.status_code == 200:
            tree = tree_resp.json()
            files = [item["path"] for item in tree.get("tree", [])[:30]]

    except httpx.HTTPError as e:
        return f"Error analyzing repo '{repo_name}': {e}"

    lang_str = ", ".join(f"{k}: {v}" for k, v in languages.items())

    return (
        f"📦 Repository: {repo['full_name']}\n"
        f"   Description: {repo.get('description') or 'N/A'}\n"
        f"   Default branch: {repo.get('default_branch', 'main')}\n"
        f"   Stars: {repo.get('stargazers_count', 0)} | Forks: {repo.get('forks_count', 0)}\n"
        f"   Languages: {lang_str or 'N/A'}\n"
        f"   Created: {repo.get('created_at', 'N/A')}\n"
        f"   Updated: {repo.get('updated_at', 'N/A')}\n\n"
        f"📁 Root files:\n   " + "\n   ".join(files) + "\n\n"
        f"📄 README (first 1500 chars):\n{readme}"
    )


@tool
def recommend_technology(requirement: str) -> str:
    """Recommend technologies based on the existing stack and a specific requirement.

    Args:
        requirement: What you need (e.g. 'deploy ML model as API', 'real-time chat').
    """
    stack_knowledge = {
        "api": {
            "recommendation": "FastAPI",
            "reason": "Already in your stack (youtube_summarizer, agents-demo). Async, auto-docs, Pydantic validation.",
            "alternatives": ["Django REST Framework (existing Django knowledge)", "Flask (simpler but less modern)"],
        },
        "frontend": {
            "recommendation": "Next.js 15 + React 19 + TypeScript",
            "reason": "Already used in youtube_summarizer. SSR, API routes, excellent DX.",
            "alternatives": ["Gradio (for ML demos)", "Streamlit (quick prototypes)"],
        },
        "database": {
            "recommendation": "PostgreSQL + Drizzle ORM (or Prisma for Next.js)",
            "reason": "PostgreSQL already in stack. Drizzle for Node, SQLAlchemy/Prisma also familiar.",
            "alternatives": ["SQLite (zero-config, great for demos)", "pgvector (for embeddings)"],
        },
        "llm": {
            "recommendation": "LangGraph + OpenRouter (DeepSeek V3 / Gemini Flash)",
            "reason": "LangGraph for stateful agents, OpenRouter for model flexibility and cost control.",
            "alternatives": ["Direct OpenAI API", "HuggingFace Inference API", "Ollama (local)"],
        },
        "deploy": {
            "recommendation": "Docker + VPS (Hostinger) or HuggingFace Spaces",
            "reason": "Docker already in workflow. HF Spaces for free Gradio hosting.",
            "alternatives": ["Railway", "Fly.io", "AWS ECS (for enterprise)"],
        },
        "agent": {
            "recommendation": "LangGraph with ReAct pattern",
            "reason": "Already demonstrated in Prometheus/Arquimedes/Atlas. Production-ready, LangSmith tracing.",
            "alternatives": ["CrewAI (multi-agent)", "AutoGen (Microsoft)", "Haystack"],
        },
        "rag": {
            "recommendation": "LangChain + pgvector + cross-encoder reranking",
            "reason": "Arquimedes project uses this pattern. Production-proven.",
            "alternatives": ["ChromaDB (simpler)", "Pinecone (managed)", "Qdrant"],
        },
        "tts": {
            "recommendation": "ElevenLabs API (quality) or Kokoro-TTS via HF (free)",
            "reason": "Both already integrated in your scripts (tts_elevenlabs.py, tts_kokoro_hf.py).",
            "alternatives": ["Google Cloud TTS", "Azure Speech", "Bark (open source)"],
        },
        "chat": {
            "recommendation": "LangGraph chatbot with MemorySaver + summarization",
            "reason": "Production pattern from agents-demo. Handles long conversations efficiently.",
            "alternatives": ["Chainlit (UI framework)", "Vercel AI SDK (for Next.js)"],
        },
        "ml": {
            "recommendation": "HuggingFace Transformers + PyTorch",
            "reason": "HF ecosystem already in use (Spaces, models). PyTorch is industry standard.",
            "alternatives": ["TensorFlow/Keras", "scikit-learn (classical ML)", "ONNX Runtime"],
        },
    }

    req_lower = requirement.lower()
    matched = None
    for key, info in stack_knowledge.items():
        if key in req_lower:
            matched = info
            break

    if matched:
        alts = "\n".join(f"     • {a}" for a in matched["alternatives"])
        return (
            f"🎯 Recommendation: {matched['recommendation']}\n\n"
            f"   Why: {matched['reason']}\n\n"
            f"   Alternatives:\n{alts}"
        )

    return (
        f"For '{requirement}', here's a general approach based on your stack:\n"
        f"  • Backend: FastAPI (Python) or Next.js API routes (TypeScript)\n"
        f"  • AI/LLM: LangGraph + OpenRouter\n"
        f"  • Database: PostgreSQL or SQLite\n"
        f"  • Deploy: Docker → VPS or HuggingFace Spaces\n"
        f"  • Observability: LangSmith for AI, standard logging for services"
    )


all_tools = [
    search_github_repos,
    search_hf_spaces,
    analyze_project_structure,
    recommend_technology,
]
