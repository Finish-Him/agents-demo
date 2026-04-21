# 🛰️ Referência da API

Servidor FastAPI em `api.py` · porta padrão `8000` · OpenAPI auto-gerada
em `/docs` e `/redoc`.

---

## 🔌 Endpoints

### `GET /health`

Liveness check + inventário de agentes.

```json
{ "status": "ok", "agents": ["prometheus", "arquimedes", "atlas"] }
```

### `GET /agents`

Metadados de cada agente registrado (a UI React consome para renderizar
as abas e os exemplos).

```json
{
  "arquimedes": {
    "name": "Arquimedes",
    "description": "Tutor adaptativo de matemática para ML — álgebra linear, cálculo, probabilidade e estatística. RAG sobre Strang/Deisenroth/OpenStax; derivações passo a passo.",
    "lang": "pt-BR",
    "examples": [
      "Explique autovetores com uma analogia geométrica e cite o livro-texto.",
      "Derive passo a passo o gradiente da função de perda MSE.",
      "..."
    ]
  },
  "prometheus": { "...": "..." },
  "atlas":      { "...": "..." }
}
```

### `GET /models`

Modelos disponíveis no seletor da UI.

```json
{
  "default": "qwen/qwen3-235b-a22b",
  "available": [
    { "id": "qwen/qwen3-235b-a22b",         "name": "Qwen3 235B (OpenRouter)",  "speed": "fast" },
    { "id": "deepseek/deepseek-chat-v3-0324","name": "DeepSeek V3 (OpenRouter)","speed": "medium" },
    { "id": "gemini-2.0-flash",              "name": "Gemini 2.0 Flash (Google)","speed": "fast" },
    { "id": "gpt-4o-mini",                   "name": "GPT-4o Mini (OpenAI)",    "speed": "fast" },
    { "id": "claude-sonnet-4-20250514",      "name": "Claude Sonnet 4 (Anthropic)","speed": "medium" },
    { "id": "hf/Qwen/Qwen2.5-7B-Instruct",   "name": "Qwen2.5 7B (HF Inference)","speed": "medium" }
  ]
}
```

### `POST /chat/{agent_name}`

Chat bloqueante — retorna a resposta completa quando o graph termina.

**Body** (`ChatRequest`):
```json
{
  "message": "Explique autovetores com uma analogia geométrica.",
  "thread_id": "optional-uuid",
  "user_id": "default-user",
  "model_name": "openai/gpt-4o-mini"
}
```

**Response** (`ChatResponse`):
```json
{
  "response": "Um autovetor é uma direção que a transformação...",
  "thread_id": "generated-or-passed-through",
  "agent": "arquimedes"
}
```

❌ **404** se `agent_name` não estiver em `["prometheus","arquimedes","atlas"]`.

### `POST /chat/{agent_name}/stream`

Mesmo body; retorna Server-Sent Events.

**Tipos de eventos:**

| 📌 event | 📦 data | 💡 quando dispara |
|---|---|---|
| `metadata` | `{"thread_id":"...","agent":"..."}` | primeiro evento, sempre |
| `token` | fragmento de texto do LLM | só tokens do nó `assistant` (memória e sumarização são filtrados) |
| `tool_start` | nome da tool prestes a executar | antes do `ToolNode` rodar |
| `tool_end` | nome da tool que terminou | depois do `ToolNode` |
| `done` | vazio | fim do stream |

**Curl de exemplo:**
```bash
curl -N -X POST http://localhost:8000/chat/arquimedes/stream \
  -H "Content-Type: application/json" \
  -d '{"message":"Explique autovetores geometricamente.","thread_id":"demo-1"}'
```

---

## 🧵 Threading e memória

- 🧵 **`thread_id`** — escopo da conversa. Passe o mesmo valor entre
  requisições para manter histórico. Omita no primeiro turno e o
  servidor gera um UUID (retornado no primeiro evento `metadata` ou
  no body de `/chat/{agent_name}`).
- 👤 **`user_id`** — escopo do Store de longo prazo. Dois threads
  diferentes com o mesmo `user_id` compartilham o perfil do usuário
  (fatos de compliance em Prometheus, nível do aluno em Arquimedes).

---

## 🎨 Frontend estático

Se `frontend/dist/` existir, o servidor também serve a SPA React:

- `GET /assets/*` → bundles JS/CSS compilados
- qualquer outro path → `index.html` (fallback SPA)

Prefixos de API (`health`, `agents`, `models`, `chat`, `docs`,
`redoc`, `openapi.json`) são excluídos do fallback para preservar o
comportamento FastAPI.

---

## 🔓 CORS

Aberto em dev: `allow_origins=["*"]`. **Restringir em produção.**
