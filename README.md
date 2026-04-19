<div align="center">

# Agents Demo

**Three production-ready LangGraph agents with a React UI, FastAPI backend, and Docker deployment.**

[![Python Tests](https://github.com/Finish-Him/agents-demo/actions/workflows/ci.yml/badge.svg)](https://github.com/Finish-Him/agents-demo/actions/workflows/ci.yml)

![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-blue)
![React](https://img.shields.io/badge/React-18.3-61DAFB?logo=react)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)
![Tailwind](https://img.shields.io/badge/Tailwind-3.4-06B6D4?logo=tailwindcss)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker)

*Built by **Moisés Costa** for the Factored.ai Senior Software Engineer (GenAI) interview.*

</div>

---

## Agents

| Agent | Domain | Tools | Key Patterns |
|-------|--------|-------|--------------|
| **Prometheus** | AI governance & data-privacy (GDPR, CCPA, EU AI Act) | 5 — regulations, penalties, risk levels, checklists, deadlines | ReAct + Summarization + Long-term Memory |
| **Archimedes** | Adaptive AI tutor (ML, Python, deep learning, agents) | 4 — assess level, generate exercises, explain concepts, resources | ReAct + Student Profile Memory + Adaptive Routing |
| **Atlas** | Tech stack consultant (GitHub + HuggingFace APIs) | 4 — search GitHub repos, HF Spaces, project analyzer, tech recommender | ReAct + External API Tools |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     React SPA (Vite)                        │
│       Zustand store ─ SSE client ─ Tailwind dark UI         │
└────────────────────────┬────────────────────────────────────┘
                         │ SSE (token/tool_start/tool_end/done)
┌────────────────────────▼────────────────────────────────────┐
│               FastAPI server (api.py :8000)                 │
│   /health  /agents  /models  /chat/{agent}  + static SPA   │
└───┬───────────────┬───────────────┬─────────────────────────┘
    │               │               │
┌───▼───┐     ┌─────▼─────┐   ┌────▼────┐
│Prometheus│   │Archimedes │   │  Atlas  │
│ 5 tools │   │  4 tools  │   │ 4 tools │
└───┬───┘     └─────┬─────┘   └────┬────┘
    │               │               │
┌───▼───────────────▼───────────────▼─────┐
│      shared/ (LLM factory, config,      │
│         MemorySaver, InMemoryStore)      │
└───────────────┬─────────────────────────┘
                │
    ┌───────────▼───────────────┐
    │  Multi-LLM (OpenRouter,   │
    │  OpenAI, Anthropic, Gemini)│
    └───────────────────────────┘
```

### Directory Structure

```
agents-demo/
├── shared/              # LLM factory, config, memory singletons
├── prometheus/          # AI compliance agent (agent.py, tools.py, prompts.py)
├── arquimedes/          # AI tutor agent
├── atlas/               # Stack consultant agent
├── frontend/            # React 18 + Vite + Tailwind + Zustand
│   ├── src/             # Components, stores, API client
│   ├── e2e/             # Playwright E2E tests (29 specs)
│   └── playwright.config.ts
├── tests/               # pytest unit tests (99 tests)
├── docs/                # Extended docs (architecture, agents, API)
├── .github/workflows/   # CI (pytest + build) + Deploy (SSH + Docker)
├── api.py               # FastAPI server (REST + SSE streaming)
├── ui.py                # Gradio web UI (fallback)
├── Dockerfile           # Multi-stage (Node build → Python serve)
├── docker-compose.yml   # Production deployment
└── langgraph.json       # LangGraph Studio config
```

See [docs/](docs/) for architecture deep-dive, per-agent reference, and full API docs.

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Agent framework** | LangGraph 0.2+ | Stateful graph orchestration, checkpointer, memory store |
| **LLM abstraction** | LangChain | Multi-provider LLM, tools, messages |
| **Observability** | LangSmith | End-to-end tracing |
| **API** | FastAPI | REST + SSE streaming, static file serving |
| **Frontend** | React 18 + Vite + Tailwind 3.4 + Zustand | Dark-themed SPA with real-time streaming |
| **Testing** | pytest (99 tests) + Playwright (29 E2E specs) | Unit + integration + end-to-end |
| **CI/CD** | GitHub Actions | Auto test + deploy on push to main |
| **Deployment** | Docker multi-stage | Node.js builds frontend → Python serves all |
| **LLMs** | Qwen3 235B, DeepSeek V3, Gemini 2.0, GPT-4o Mini, Claude Sonnet 4 | 5 models selectable in UI |

## Quick Start

### 1. Setup

```bash
git clone https://github.com/Finish-Him/agents-demo.git
cd agents-demo
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
# .\.venv\Scripts\Activate.ps1  # Windows
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your API keys
```

| Key | Required | Provider |
|-----|----------|----------|
| `OPENROUTER_API_KEY` | Yes | Default LLM provider |
| `OPENAI_API_KEY` | Optional | GPT-4o Mini |
| `ANTHROPIC_API_KEY` | Optional | Claude Sonnet 4 |
| `GOOGLE_API_KEY` | Optional | Gemini 2.0 Flash |
| `LANGSMITH_API_KEY` | Optional | Tracing |

### 3. Run Locally

```bash
# Backend + React UI (production-like)
python api.py
# → http://localhost:8000 (React UI)
# → http://localhost:8000/docs (Swagger)
```

```bash
# Gradio UI (alternative)
python ui.py
# → http://localhost:7860
```

```bash
# LangGraph Studio (visual debugging)
langgraph dev
# → http://localhost:8123
```

### 4. Docker

```bash
docker compose up -d
# → http://localhost:8000 (React UI + API)
# → http://localhost:7860 (Gradio fallback)
```

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check — returns `{status, agents}` |
| `GET` | `/agents` | Agent metadata, descriptions, example prompts |
| `GET` | `/models` | Available LLM models |
| `POST` | `/chat/{agent_name}` | Chat with agent — returns SSE stream |

### SSE Event Types

| Event | Payload | Description |
|-------|---------|-------------|
| `metadata` | `{thread_id}` | Session ID for conversation continuity |
| `token` | `{content}` | Streamed text token from LLM |
| `tool_start` | `{name, input}` | Tool invocation started |
| `tool_end` | `{name, output}` | Tool invocation completed |
| `done` | `{full_response}` | Stream finished |

### Example

```bash
curl -N -X POST http://localhost:8000/chat/prometheus \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the GDPR penalties?", "thread_id": "test-1"}'
```

## Testing

### Python Unit Tests (99 tests)

```bash
pip install -r requirements.txt
python -m pytest tests/ -v
```

Covers: LLM factory, configuration, all 13 agent tools, API endpoints.

### Playwright E2E Tests (29 specs)

```bash
cd frontend
npm install
npx playwright install chromium
npx playwright test
```

Covers: app loading, agent navigation, chat interaction, accessibility.

## CI/CD

Push to `main` triggers:

1. **CI** (`.github/workflows/ci.yml`) — Python tests + Frontend TypeScript check + Vite build
2. **Deploy** (`.github/workflows/deploy.yml`) — SSH into VPS → `git pull` → `docker compose build` → health check

Required GitHub Secrets: `VPS_HOST`, `VPS_USER`, `VPS_PASSWORD`.

## LangGraph Patterns Demonstrated

| Pattern | Agent | Implementation |
|---------|-------|---------------|
| **ReAct Loop** | All 3 | `tools_condition` + `ToolNode` + loop edge |
| **Conversation Memory** | All 3 | `MemorySaver` checkpointer with `thread_id` |
| **Summarization** | Prometheus, Archimedes | Auto-compress after 10 messages, `RemoveMessage` |
| **Long-term Memory** | Prometheus, Archimedes | `InMemoryStore` with namespace per user |
| **Profile Extraction** | Prometheus, Archimedes | LLM-based fact extraction to Store |
| **Custom State** | Prometheus, Archimedes | Extended `MessagesState` with `summary` field |
| **Configuration** | All 3 | `@dataclass` config with `from_runnable_config()` |
| **External API Tools** | Atlas | `httpx` calls to GitHub + HuggingFace APIs |
| **Conditional Routing** | All 3 | `add_conditional_edges` with `Literal` returns |

## Deploy to VPS

```bash
ssh root@<VPS_IP>
git clone https://github.com/Finish-Him/agents-demo.git
cd agents-demo
cp .env.example .env   # Edit with production keys
docker compose up -d

# Verify
curl http://localhost:8000/health
```

## Author

**Moisés Costa** — [GitHub](https://github.com/Finish-Him)

## License

MIT
