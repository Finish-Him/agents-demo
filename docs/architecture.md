# 🏗️ Arquitetura

Visão de alto nível de como o `agents-demo` se conecta.

---

## 🧱 Diagrama de componentes

```text
┌─────────────────────────┐      ┌─────────────────────────┐
│  React (Vite + Tailwind │      │  Gradio UI (ui.py)      │
│  + framer-motion+KaTeX) │      │  3 abas, 1 por agente   │
│  frontend/dist          │      │                         │
└──────────┬──────────────┘      └──────────┬──────────────┘
           │ HTTP + SSE                     │ in-process
           ▼                                ▼
┌──────────────────────────────────────────────────────────┐
│  FastAPI (api.py)                                        │
│  /health  /agents  /models  /chat/{name}  /chat/.../stream │
└──────────┬───────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────┐
│  LangGraph runtime — 3 graphs compilados                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │ Prometheus  │  │ Arquimedes  │  │   Atlas     │       │
│  │ 4 nodes     │  │ 5 nodes +   │  │ 3 nodes     │       │
│  │             │  │ derivation  │  │             │       │
│  │             │  │ subgraph    │  │             │       │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘       │
└─────────┼─────────────────┼─────────────────┼────────────┘
          │                 │                 │
          ▼                 ▼                 ▼
   ┌──────────┐   ┌────────────────────┐   ┌──────────┐
   │ tools.py │   │ tools/ (9 tools)   │   │ tools.py │
   │compliance│   │ teaching · RAG ·   │   │GitHub+HF │
   │          │   │ SymPy · plot ·     │   │          │
   │          │   │ derive · LoRA      │   │          │
   └──────────┘   └─────────┬──────────┘   └──────────┘
                            │
              ┌─────────────┴───────────────┐
              ▼                             ▼
      ┌──────────────┐         ┌────────────────────┐
      │ ChromaDB RAG │         │ shared/llm.py      │
      │ BM25 + denso │         │ multi-provider     │
      │ + RRF fusion │         │ OpenRouter/OpenAI/ │
      │ + LaTeX-aware│         │ Anthropic/Google/  │
      │ chunker      │         │ Azure/HF Inference │
      └──────────────┘         └────────────────────┘
```

📡 Camada extra opcional — **MCP server** (`arquimedes/mcp_server/`)
expõe as mesmas 9 tools do Arquimedes via stdio ou SSE para clientes
externos (Claude Desktop, Cursor, Cline). Schemas introspectados do
`args_schema` Pydantic — paridade automática.

---

## 💾 Estado e memória

Duas camadas de persistência, ambas injetadas no compile-time do graph
(`shared/memory.py`):

| Camada | Backend padrão | Backend produção | Escopo | Propósito |
|---|---|---|---|---|
| 🧵 **Checkpointer** | `MemorySaver` | `AsyncSqliteSaver` ou `PostgresSaver` | por `thread_id` | histórico da conversa, resumability |
| 🧠 **Store** | `SemanticStore` (Chroma) | `PostgresSemanticStore` (pgvector / Supabase) | por `(namespace, user_id)` | perfil de longo prazo recuperado por similaridade |

Ambos são singletons — todo agente compilado por `builder.compile()`
compartilha o mesmo checkpointer/store. Para trocar em produção, edite
apenas `shared/memory.py` (env vars `MEMORY_BACKEND`,
`POSTGRES_URL`, `SQLITE_CHECKPOINT_PATH`).

---

## ⚙️ Injeção de configuração

`shared/configuration.py` define um `@dataclass Configuration`:

- 🎯 `model_name` — sobrescrevível por requisição
- 👤 `user_id` — segrega namespaces do Store

A dataclass é passada como `config_schema=Configuration` no `builder`.
Cada nó lê via `Configuration.from_runnable_config(config)`. Overrides
de request fluem pelo campo `configurable` do `RunnableConfig`.

---

## 🧠 Fábrica de LLMs (`shared/llm.py`)

Único ponto de entrada: `get_llm(model: str | None = None)`. Roteamento
por prefixo:

| Prefixo | Provider | Wrapper |
|---|---|---|
| `qwen/`, `deepseek/`, sem prefixo | OpenRouter | `ChatOpenAI(base_url=...)` |
| `openai/`, `gpt-`, `o1` | OpenAI | `ChatOpenAI` |
| `anthropic/`, `claude-` | Anthropic | `ChatAnthropic` |
| `gemini`, `google/` | Google | `ChatGoogleGenerativeAI` |
| `azure/` | Azure OpenAI | `AzureChatOpenAI` |
| `hf/`, `huggingface/` | HF Inference API | `ChatHuggingFace` |

Default: `qwen/qwen3-235b-a22b` (barato, rápido, suporta function-calling).
Override por requisição via `ChatRequest.model_name`.

---

## 🌊 Fluxo de uma requisição (`POST /chat/{agent}/stream`)

1. Handler FastAPI monta `RunnableConfig` com `thread_id`, `user_id`,
   `model_name`.
2. `graph.astream_events(..., version="v2")` é invocado.
3. SSE são emitidos com **filtro por `langgraph_node == 'assistant'`**
   — só tokens do assistente vão para o cliente; `write_memory` e
   `summarize_conversation` não vazam strings internas:
   - `metadata` (thread_id, agent)
   - `token` (cada chunk do LLM do assistant)
   - `tool_start` / `tool_end` (lifecycle de tools)
   - `done`
4. Frontend renderiza tokens incrementalmente (`react-markdown` +
   `rehype-katex`), pinta badges de tools com framer-motion.

---

## 🎨 Frontend ↔ Backend

O build React (`frontend/dist/`) é servido pelo mesmo processo FastAPI
via `StaticFiles` + fallback SPA (`api.py`). Prefixos da API (`health`,
`agents`, `chat`, `docs`, `redoc`) são excluídos do fallback para que
o FastAPI vença.

Em prod com nginx, o reverse-proxy roteia `:80 → :8000` mantendo
`proxy_buffering off` (essencial para SSE).

---

## 🤔 Por quê dessa forma

- 🧩 **Single process em dev** — mais fácil rodar, mais fácil demonstrar.
- 🔌 **LLM multi-provider** — sem vendor lock-in; fallback gracioso.
- 🌊 **Streaming-first** — todo endpoint que pode, transmite via SSE.
- 🧠 **Memória dividida** — thread state (volátil) vs perfil de usuário
  (durável). Casa com os patterns de referência da doc do LangGraph.
- 🛠️ **Tools como source of truth única** — cada `@tool` em
  `arquimedes/tools/` é consumida por LangGraph **e** pelo MCP server
  sem duplicação.
