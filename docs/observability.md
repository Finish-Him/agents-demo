# Observability — LangSmith + logs + metrics

Every LLM call, tool invocation, and graph node emits a trace to
LangSmith out of the box. This doc explains how to turn it on, what's
captured, and how to reason about latency / token spend during the demo.

## Setup

```bash
# .env
LANGSMITH_API_KEY=lsv2_pt_...        # required to upload traces
LANGSMITH_TRACING=true               # toggles OpenTelemetry span upload
LANGSMITH_PROJECT=agents-demo-arquimedes   # one project per deployment
```

`shared/llm.py` calls `load_dotenv()` at import time so any Python entry
point (`python api.py`, `python -m arquimedes.mcp_server`, `pytest`,
Colab notebook) picks the same credentials and project label.

## What you'll see in LangSmith

For a single chat turn (`POST /chat/arquimedes`), the trace tree looks
like this (one per user request):

```
RunnableSequence                     ← LCEL assistant chain
├── ChatPromptTemplate               ← system + messages assembled
├── ChatOpenAI (or AzureOpenAI, ...) ← token stream + tool_calls
├── ToolNode                         ← zero or more tools
│   ├── search_knowledge_base
│   ├── solve_symbolic
│   └── ...
├── RunnableSequence (write_memory)  ← structured extractor
│   └── ChatOpenAI (with_structured_output)
└── should_continue                  ← conditional edge, cheap
```

If the entry router decided to pull RAG first, you'll also see a
`rag_retrieve` span with the Chroma similarity_search latency. The
`step_by_step_derive` tool expands into a sub-trace with `plan`,
`step`, and `verify` nodes — one-click drilldown from the parent.

## Fetching traces programmatically

```python
from langsmith import Client
c = Client()
runs = c.list_runs(project_name="agents-demo-arquimedes", limit=20)
for r in runs:
    print(r.name, r.status, r.total_tokens, r.latency)
```

This is the same API `tests/` uses to verify tracing in CI when
`LANGSMITH_API_KEY` is set as a secret.

## Metrics worth watching

| Metric | Where to look | Why |
|---|---|---|
| Per-turn latency | `RunnableSequence` duration | Tail goal: P95 < 4 s for streaming. |
| Tokens per turn | `ChatOpenAI` usage | Cost control and context limit. |
| Tool failure rate | filter `status = error` | Broken tools are the #1 trust issue. |
| RAG hit rate | count of `rag_retrieve` spans | Validates the entry router heuristic. |
| Memory writes | `write_memory` success rate | Ensures the SemanticStore is getting populated. |

## Log channels

- **FastAPI** — uvicorn access log on stdout. Structured body is in the
  response payload; SSE events don't log bodies by default.
- **Graph** — LangGraph logs at INFO when `LANGGRAPH_LOG_LEVEL=INFO`.
- **MCP server** — `arquimedes.mcp_server` sends everything to
  **stderr** (stdout is reserved for JSON-RPC frames).
- **Embedding + RAG** — Chroma / sentence-transformers log to stdout;
  suppress with `TRANSFORMERS_VERBOSITY=error` when running MCP.

## Production checklist

- Set `LANGSMITH_PROJECT` per environment (`-staging`, `-prod`, etc.).
- Scrub PII at the tracer boundary — see the LangSmith `hide_inputs` /
  `hide_outputs` env vars if a tool receives sensitive data.
- Alert on P95 latency and `write_memory` error rate with whatever
  platform you already use (Grafana/Datadog); LangSmith's webhook output
  can target any HTTP endpoint.

## Cost hygiene

- `temperature=0` on the memory extractor and router so they're
  reproducible and cacheable.
- Cap `HF_MAX_NEW_TOKENS` and the summariser prompt size.
- Use LangSmith's "Dataset" feature to record canonical 20-turn
  sessions for regression-testing new prompts or models.
