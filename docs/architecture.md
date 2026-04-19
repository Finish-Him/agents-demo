# Architecture

High-level view of how `agents-demo` is wired together.

## Component diagram (textual)

```
┌─────────────────────────┐      ┌─────────────────────────┐
│   React frontend        │      │   Gradio UI (ui.py)     │
│   (frontend/dist)       │      │   3 tabs, 1 per agent   │
└──────────┬──────────────┘      └──────────┬──────────────┘
           │ HTTP + SSE                     │ in-process
           ▼                                ▼
┌──────────────────────────────────────────────────────────┐
│   FastAPI server (api.py)                                │
│   /health  /agents  /models  /chat/{name}  /chat/.../stream │
└──────────┬───────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────┐
│   LangGraph runtime — 3 compiled graphs                  │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│   │ Prometheus  │  │ Arquimedes  │  │   Atlas     │      │
│   │  (5 nodes)  │  │  (5 nodes)  │  │  (3 nodes)  │      │
│   └──────┬──────┘  └──────┬──────┘  └──────┬──────┘      │
└──────────┼─────────────────┼─────────────────┼───────────┘
           │                 │                 │
           ▼                 ▼                 ▼
   ┌───────────────┐  ┌───────────────┐  ┌───────────────┐
   │ tools.py      │  │ tools.py      │  │ tools.py      │
   │ (compliance)  │  │ (tutoring)    │  │ (GitHub + HF) │
   └───────────────┘  └───────────────┘  └───────────────┘
                              │
                              ▼
                  ┌───────────────────────────┐
                  │ shared/llm.py             │
                  │ Multi-provider LLM factory │
                  │ OpenRouter / OpenAI /     │
                  │ Anthropic / Gemini        │
                  └───────────────────────────┘
```

## State & memory

Two persistence layers, both injected at graph compile time
(`shared/memory.py`):

| Layer | Implementation | Scope | Purpose |
|---|---|---|---|
| **Checkpointer** | `MemorySaver` (in-process, swappable for SQLite) | Per `thread_id` | Conversation history, resumability |
| **Store** | `InMemoryStore` | Per `(namespace, user_id)` | Long-term user profile (compliance facts, learning level, etc.) |

Both are singletons — every agent compiled by `builder.compile()` shares
the same checkpointer/store instances. To swap for production
(SQLite checkpointer, Postgres store), edit `shared/memory.py` only.

## Configuration injection

`shared/configuration.py` defines a `@dataclass Configuration` with:
- `model_name` — overridable per request
- `user_id` — segregates Store namespaces

The dataclass is passed as `config_schema=Configuration` when building the
graph. Each node reads it via `Configuration.from_runnable_config(config)`.
Request-level overrides flow through the `configurable` field of
`RunnableConfig`.

## LLM factory (`shared/llm.py`)

Single entry point: `get_llm(model: str | None = None)`. Routing by prefix:
- `qwen/...`, `deepseek/...` → OpenRouter
- `gpt-...`, `o1...` → OpenAI
- `claude-...` → Anthropic
- `gemini-...` → Google

Default: `qwen/qwen3-235b-a22b` (cheap, fast, function-calling capable).
Override per request via `ChatRequest.model_name`.

## Request flow (POST /chat/{agent}/stream)

1. FastAPI handler builds `RunnableConfig` with `thread_id`, `user_id`, `model_name`
2. `graph.astream_events(..., version="v2")` is invoked
3. Server-Sent Events emitted:
   - `metadata` (thread_id, agent name)
   - `token` (every LLM chunk)
   - `tool_start` / `tool_end` (tool execution lifecycle)
   - `done`
4. Frontend renders tokens incrementally, badges tool calls

## Frontend ↔ Backend coupling

The React build (`frontend/dist/`) is served by the same FastAPI process
via `StaticFiles` + SPA fallback (see `api.py:200-220`). API route
prefixes (`health`, `agents`, `chat`, `docs`, `redoc`) are explicitly
excluded from the SPA fallback so FastAPI's own routes win.

## Why this shape

- **Single process** in dev: easier to run, easier to demo
- **Multi-provider LLM**: no vendor lock-in; falls back gracefully
- **Streaming-first**: every endpoint that supports it streams via SSE
- **Memory split**: thread state (volatile) vs user profile (durable)
  matches the LangGraph reference patterns from the docs
