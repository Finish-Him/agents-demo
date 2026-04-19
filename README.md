# Agents Demo — Factored.ai Interview

Three functional **LangGraph** agents demonstrating ReAct tool calling, memory persistence, external API integration, and production deployment patterns.

**Built by Moisés Costa** for the Factored.ai Senior Software Engineer (GenAI) interview.

## Agents

| Agent | Domain | Pattern | Language |
|-------|--------|---------|----------|
| **Prometheus** | AI governance & data-privacy compliance (GDPR, CCPA, EU AI Act) | ReAct + Summarization + Long-term Memory | EN |
| **Archimedes** | Adaptive AI tutor (ML, Python, deep learning, LLM agents) | ReAct + Student Profile Memory + Adaptive Routing | EN |
| **Atlas** | Tech stack consultant (GitHub + HuggingFace APIs) | ReAct + External API Tools | EN |

## Architecture

```
agents-demo/
├── shared/              # Shared infra (LLM factory, config, memory)
│   ├── llm.py           # Multi-provider LLM (OpenRouter, OpenAI, Anthropic, Gemini)
│   ├── configuration.py # Configurable dataclass
│   └── memory.py        # MemorySaver + InMemoryStore singletons
├── prometheus/          # AI compliance agent
│   ├── agent.py         # LangGraph graph (5 nodes, ReAct + summarization)
│   ├── tools.py         # 5 tools (regulations, penalties, risk assessment, checklists)
│   └── prompts.py       # System prompt
├── arquimedes/          # AI tutor agent
│   ├── agent.py         # LangGraph graph (5 nodes, ReAct + profile memory)
│   ├── tools.py         # 4 tools (assess, exercise, explain, resources)
│   └── prompts.py       # System prompt
├── atlas/               # Stack specialist agent
│   ├── agent.py         # LangGraph graph (3 nodes, ReAct + API tools)
│   ├── tools.py         # 4 tools (GitHub API, HF API, project analyzer)
│   └── prompts.py       # System prompt
├── frontend/            # React + Vite SPA (served by FastAPI in prod)
│   ├── src/             # Components, stores, API client
│   └── package.json
├── docs/                # Extended documentation
│   ├── architecture.md  # System design + request flow
│   ├── agents.md        # Per-agent reference
│   └── api.md           # REST + SSE endpoint reference
├── api.py               # FastAPI server (REST + SSE streaming)
├── ui.py                # Gradio web UI (3 tabs)
├── langgraph.json       # LangGraph Studio config
├── docker-compose.yml   # Docker deployment
└── Dockerfile
```

See [docs/](docs/) for architecture, per-agent reference, and full API docs.

## Tech Stack

- **LangGraph** 0.2+ — Stateful agent orchestration (graphs, nodes, edges, checkpoints)
- **LangChain** — LLM abstraction, tools, messages
- **LangSmith** — End-to-end tracing and observability
- **Multi-LLM** — OpenRouter (default), OpenAI, Anthropic Claude, Google Gemini
- **FastAPI** — REST API with streaming support
- **Gradio** — Web UI with chat interface
- **Docker** — Containerized deployment
- **GitHub API** / **HuggingFace API** — External tool integrations

## Quick Start

### 1. Setup

```bash
cd agents-demo
python -m venv .venv

# Windows
.\.venv\Scripts\Activate.ps1

# Linux/Mac
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your API keys
```

Required keys:
- `OPENROUTER_API_KEY` — Default LLM provider
- `OPENAI_API_KEY` — OpenAI models (gpt-4o, o1, etc.)
- `ANTHROPIC_API_KEY` — Anthropic models (claude-3.5-sonnet, etc.)
- `GOOGLE_API_KEY` — Google Gemini models
- `LANGSMITH_API_KEY` — Tracing (recommended)
- `GITHUB_TOKEN` — For Atlas agent GitHub tools
- `HF_TOKEN` — For Atlas agent HuggingFace tools

### 3. Run

**Gradio UI** (recommended for demo):
```bash
python ui.py
# Open http://localhost:7860
```

**FastAPI server**:
```bash
python api.py
# API at http://localhost:8000
# Docs at http://localhost:8000/docs
```

**LangGraph Studio** (visual debugging):
```bash
langgraph dev
# Studio at http://localhost:8123
```

### 4. Docker

```bash
docker-compose up -d
# Gradio UI: http://localhost:7860
# FastAPI: http://localhost:8000
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check + list agents |
| GET | `/agents` | Agent metadata + examples |
| POST | `/chat/{agent_name}` | Chat with an agent |

### Example Request

```bash
curl -X POST http://localhost:8000/chat/prometheus \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the GDPR penalties for a data breach?", "thread_id": "test-1"}'
```

## LangGraph Patterns Demonstrated

| Pattern | Agent | Description |
|---------|-------|-------------|
| **ReAct Loop** | All 3 | `tools_condition` + `ToolNode` + loop edge |
| **Conversation Memory** | All 3 | `MemorySaver` checkpointer with `thread_id` |
| **Summarization** | Prometheus, Arquimedes | Auto-compress after 10 messages, `RemoveMessage` |
| **Long-term Memory** | Prometheus, Arquimedes | `InMemoryStore` with namespace per user |
| **Profile Extraction** | Prometheus, Arquimedes | LLM-based fact extraction to Store |
| **Custom State** | Prometheus, Arquimedes | Extended `MessagesState` with `summary` field |
| **Configuration** | All 3 | `@dataclass` config schema with `from_runnable_config()` |
| **External API Tools** | Atlas | `httpx` calls to GitHub + HuggingFace APIs |
| **Conditional Routing** | All 3 | `add_conditional_edges` with `Literal` returns |

## Deployment to VPS

```bash
# SSH to Hostinger VPS
ssh root@187.77.37.158

# Clone and deploy
git clone https://github.com/Finish-Him/agents-demo.git
cd agents-demo
cp .env.example .env  # Edit with production keys
docker-compose up -d
```

## License

MIT
