# API Reference

FastAPI server in `api.py`. Default port `8000`. Auto-generated OpenAPI
docs available at `/docs` and `/redoc`.

## Endpoints

### `GET /health`

Liveness check + agent inventory.

```json
{ "status": "ok", "agents": ["prometheus", "arquimedes", "atlas"] }
```

### `GET /agents`

Metadata for every registered agent (used by the UI to render tabs and
example prompts).

```json
{
  "prometheus": {
    "name": "Prometheus",
    "description": "AI governance and data-privacy compliance specialist...",
    "lang": "en",
    "examples": ["What are the GDPR penalties for a data breach?", "..."]
  },
  "arquimedes": { ... },
  "atlas":      { ... }
}
```

### `GET /models`

Available LLM models for the picker.

```json
{
  "default": "qwen/qwen3-235b-a22b",
  "available": [
    { "id": "qwen/qwen3-235b-a22b", "name": "Qwen3 235B (OpenRouter)", "speed": "fast" },
    { "id": "deepseek/deepseek-chat-v3-0324", "name": "DeepSeek V3 (OpenRouter)", "speed": "medium" },
    { "id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash (Google)", "speed": "fast" },
    { "id": "gpt-4o-mini", "name": "GPT-4o Mini (OpenAI)", "speed": "fast" },
    { "id": "claude-sonnet-4-20250514", "name": "Claude Sonnet 4 (Anthropic)", "speed": "medium" }
  ]
}
```

### `POST /chat/{agent_name}`

Blocking chat — returns the full response when the graph finishes.

**Request body** (`ChatRequest`):
```json
{
  "message": "What are the GDPR penalties for a data breach?",
  "thread_id": "optional-uuid",
  "user_id": "default-user",
  "model_name": "qwen/qwen3-235b-a22b"
}
```

**Response** (`ChatResponse`):
```json
{
  "response": "Under GDPR, fines for a data breach...",
  "thread_id": "generated-or-passed-through",
  "agent": "prometheus"
}
```

**404** if `agent_name` not in `["prometheus", "arquimedes", "atlas"]`.

### `POST /chat/{agent_name}/stream`

Same body as `/chat/{agent_name}`. Returns Server-Sent Events.

**Event types**:

| event | data |
|---|---|
| `metadata` | `{"thread_id": "...", "agent": "..."}` (sent first) |
| `token` | a string fragment of the LLM response |
| `tool_start` | tool name about to execute |
| `tool_end` | tool name that just finished |
| `done` | empty payload — stream complete |

**Curl example**:
```bash
curl -N -X POST http://localhost:8000/chat/prometheus/stream \
  -H "Content-Type: application/json" \
  -d '{"message":"What are the GDPR penalties for a data breach?","thread_id":"demo-1"}'
```

## Threading & memory

- **`thread_id`** scopes the conversation — pass the same value across
  requests to maintain history. Omit it on first turn and the server
  generates a UUID (returned in the response / first `metadata` event).
- **`user_id`** scopes the long-term Store namespace. Two different
  threads with the same `user_id` will share the agent's user profile
  (Prometheus compliance facts, Arquimedes student level).

## Static frontend

If `frontend/dist/` exists, the API server also serves the React SPA:
- `/assets/*` — compiled JS/CSS bundles
- any other path → `index.html` (SPA fallback)

API route prefixes (`health`, `agents`, `models`, `chat`, `docs`,
`redoc`, `openapi.json`) are excluded from the fallback so they keep
their FastAPI behavior.

## CORS

Wide-open in dev: `allow_origins=["*"]`. Tighten for prod.
