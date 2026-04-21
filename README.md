<div align="center">

# 🎓 Arquimedes — Tutor de Matemática para ML

**Agente LangGraph adaptativo demonstrando 9 conceitos de AI Engineering
em produção** — desenvolvido para a entrevista técnica
**[Mouts IT](https://mouts.com.br/) × [AmBev](https://www.ambev.com.br/)**.

[![CI](https://github.com/Finish-Him/agents-demo/actions/workflows/ci.yml/badge.svg?branch=claude/arquimedes-math-agent-Mj90C)](https://github.com/Finish-Him/agents-demo/actions/workflows/ci.yml)
![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-6366f1)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)
![React](https://img.shields.io/badge/React-18.3-61DAFB?logo=react)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python)
![Tests](https://img.shields.io/badge/tests-142_passing-10b981)
![License](https://img.shields.io/badge/license-MIT-f59e0b)

</div>

---

## 🎯 O que é

Um tutor de IA que ensina **matemática para machine learning** —
álgebra linear, cálculo, probabilidade e estatística — usando, em
um único codebase, **9 técnicas que todo AI Engineer precisa dominar**:

| 🧩 Conceito | 📍 Onde está |
|---|---|
| 1️⃣ **LangChain** (LCEL + Pydantic) | `arquimedes/chains.py` · `arquimedes/schemas.py` |
| 2️⃣ **LangGraph** (router + subgraph) | `arquimedes/agent.py` · `arquimedes/subgraphs/derivation.py` |
| 3️⃣ **RAG** (BM25 + denso, Reciprocal Rank Fusion) | `arquimedes/rag/retrieval.py` |
| 4️⃣ **Chunks** (LaTeX-aware + hierárquico) | `arquimedes/rag/chunking.py` |
| 5️⃣ **Fine-tuning** (QLoRA em GSM8K) | `arquimedes/finetuning/` |
| 6️⃣ **Tools** (9 funções `@tool`) | `arquimedes/tools/` |
| 7️⃣ **MCP** (stdio + SSE) | `arquimedes/mcp_server/` |
| 8️⃣ **HuggingFace** (LLM + embeddings + adapter) | `shared/llm.py` · `arquimedes/rag/embeddings.py` |
| 9️⃣ **Memória** (semântica · Chroma ou pgvector) | `shared/memory.py` · `shared/postgres_store.py` |

> 📖 Deep-dive em [`docs/arquimedes.md`](docs/arquimedes.md) ·
> 💬 Pitch para entrevista em [`docs/interview-talking-points.md`](docs/interview-talking-points.md)

---

## 🤖 Os três agentes

| | Agente | Domínio | Tools | Padrões-chave |
|---|---|---|---|---|
| 🛡️ | **Prometheus** | Governança de IA (GDPR, EU AI Act) | 5 | ReAct + memória + sumarização |
| 🎓 | **Arquimedes** ⭐ | Matemática para ML | **9** | Router + RAG + LCEL + memória semântica + LoRA + MCP |
| 🗺️ | **Atlas** | Consultor de stack (GitHub + HF) | 4 | ReAct + APIs externas |

⭐ Arquimedes é o agente em destaque — demonstra todos os 9 conceitos
end-to-end. Os outros dois mostram que o framework é generalizável.

---

## 🏗️ Arquitetura

```text
┌────────────── React + Vite + Tailwind + framer-motion + KaTeX ──────────────┐
│  BrandBanner · Sidebar · HeroArquimedes · ChatPanel · ConceptsPanel · Footer │
└─────────────────────────────────────┬────────────────────────────────────────┘
                                      │ SSE
┌─────────────────────────────────────▼────────────────────────────────────────┐
│  FastAPI  (api.py)                                                           │
│  /health  /agents  /models  /chat/{name}  /chat/{name}/stream                │
└─────────────────────────────────────┬────────────────────────────────────────┘
                                      │
┌─────────────────────────────────────▼────────────────────────────────────────┐
│  LangGraph compiled graph                                                    │
│  START → entry_route → { rag_retrieve | assistant }                          │
│                            ↓ tools_condition                                 │
│        ToolNode (9 tools) ← assistant ← write_memory → summarize → END       │
└──────┬──────────────────┬──────────────────┬───────────────────┬─────────────┘
       │                  │                  │                   │
       ▼                  ▼                  ▼                   ▼
   ChromaDB          LLM factory     Memory (sem./PG)      MCP server
   BM25+denso        OpenRouter      MemorySaver           stdio + SSE
   + RRF             OpenAI          AsyncSqliteSaver      9 tools
   + chunker         Anthropic       SemanticStore         (mesmas do
   LaTeX-aware       Google          (Chroma)              LangGraph)
                     Azure           PostgresSemanticStore
                     HuggingFace     (pgvector)
```

📐 Detalhes em [`docs/arquimedes.md`](docs/arquimedes.md) e
[`docs/architecture.md`](docs/architecture.md).

---

## 🚀 Quickstart local

```bash
# 1. clone + ambiente
git clone https://github.com/Finish-Him/agents-demo.git
cd agents-demo
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. credenciais
cp .env.example .env
# preencha: OPENROUTER_API_KEY, OPENAI_API_KEY, HF_TOKEN, LANGSMITH_API_KEY

# 3. ingest do corpus de matemática (Strang, Deisenroth, OpenStax)
python -m arquimedes.rag.ingest --reset

# 4. sobe o backend + serve a SPA React
python api.py
# → http://localhost:8000        UI
# → http://localhost:8000/docs   Swagger
```

| Comando opcional | O que faz |
|---|---|
| `langgraph dev` | LangGraph Studio (debug visual em :8123) |
| `python -m arquimedes.mcp_server` | MCP server stdio (Claude Desktop / Cursor / Cline) |
| `python -m arquimedes.mcp_server --sse --port 8765` | MCP via HTTP/SSE |
| `python ui.py` | Gradio fallback UI (:7860) |
| `cd frontend && npm run dev` | Vite dev server (:5173) com hot reload |

---

## 🌐 Deploy

### Opção 1 — VPS Hostinger via SSH (5 min)

```bash
ssh root@187.77.37.158
curl -sLO https://raw.githubusercontent.com/Finish-Him/agents-demo/claude/arquimedes-math-agent-Mj90C/deploy/bootstrap.sh
bash bootstrap.sh                # cria .env e para
nano /opt/agents-demo/.env       # cole as chaves
bash /opt/agents-demo/deploy/bootstrap.sh
```

### Opção 2 — GitHub Actions (zero terminal)

1. Settings → Secrets and variables → Actions → adicione:
   - `VPS_HOST`, `VPS_USER`, `VPS_PASSWORD`
   - `OPENROUTER_API_KEY`, `OPENAI_API_KEY`, `HF_TOKEN`, `LANGSMITH_API_KEY`
2. Actions tab → **Deploy** → Run workflow → branch
   `claude/arquimedes-math-agent-Mj90C` → Run.

📋 Detalhes em [`deploy/README.md`](deploy/README.md).

---

## 🧪 Testes

```bash
# Python (142 testes — unitários + integração + smoke MCP)
python -m pytest tests/ -q

# Frontend E2E (Playwright)
cd frontend
npm install
npx playwright install chromium
npx playwright test
```

Cobertura: tools de ensino · LLM factory · RAG (chunking + retrieval)
· memória semântica (Chroma + Postgres mockado) · Pydantic schemas
· MCP roundtrip · API endpoints · streaming SSE.

---

## 🔗 Stack completa

| Camada | Tecnologia |
|---|---|
| 🤖 Agent framework | LangGraph 0.2+ |
| 🔗 LLM abstraction | LangChain (LCEL + Pydantic structured output) |
| 🧠 LLM providers | OpenRouter · OpenAI · Anthropic · Google · Azure · HuggingFace |
| 🔍 RAG | ChromaDB · BM25 (`rank-bm25`) · `text-embedding-3-small` ou MiniLM |
| 💾 Memória prod | Postgres + pgvector (Supabase) — fallback Chroma local |
| 🛠️ Math tools | SymPy · matplotlib · NumPy |
| 🔧 Fine-tuning | PEFT (QLoRA 4-bit) · TRL (`SFTTrainer`) · `bitsandbytes` |
| 🔌 Interop | MCP (`mcp>=1.0`) — stdio + SSE |
| 🌐 API | FastAPI · `sse-starlette` · `astream_events(v2)` |
| 🎨 Frontend | React 18 · Vite · TypeScript · Tailwind · Zustand · framer-motion · KaTeX |
| 📊 Observabilidade | LangSmith (tracing online) |
| 🚢 CI/CD | GitHub Actions · Docker Compose · Hostinger VPS · nginx (SSE-safe) |

---

## 📚 Documentação

| Arquivo | Para |
|---|---|
| 📖 [`docs/arquimedes.md`](docs/arquimedes.md) | Deep-dive da arquitetura |
| 📖 [`docs/arquimedes-rag.md`](docs/arquimedes-rag.md) | Corpus + chunking + retrieval |
| 📖 [`docs/arquimedes-mcp.md`](docs/arquimedes-mcp.md) | Setup MCP nos clientes |
| 📖 [`docs/observability.md`](docs/observability.md) | LangSmith + métricas |
| 📖 [`docs/interview-talking-points.md`](docs/interview-talking-points.md) | Pitch por conceito |
| 📖 [`docs/agents.md`](docs/agents.md) | Os 3 agentes lado a lado |
| 📖 [`docs/architecture.md`](docs/architecture.md) | Diagrama completo |
| 📖 [`docs/api.md`](docs/api.md) | Referência REST/SSE |
| 📖 [`arquimedes/finetuning/README.md`](arquimedes/finetuning/README.md) | Pipeline LoRA |
| 📖 [`deploy/README.md`](deploy/README.md) | Bootstrap VPS |
| 📋 [`TODO.md`](TODO.md) | Roadmap pendente |
| 🤝 [`CONTRIBUTING.md`](CONTRIBUTING.md) | Como contribuir |
| 📜 [`CHANGELOG.md`](CHANGELOG.md) | Histórico |

---

## 👤 Autor & contexto

**Moisés Costa** — desenvolvido como demonstração técnica para o
processo seletivo de **AI Engineer** da
[Mouts IT](https://mouts.com.br/) com o cliente
[AmBev](https://www.ambev.com.br/).

📜 Licença: [MIT](LICENSE)
