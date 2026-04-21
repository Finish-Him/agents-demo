# Arquimedes MCP Server

The same `@tool`-decorated functions that power the LangGraph tutor are
re-exposed over the [Model Context Protocol] so Claude Desktop, Cursor,
Cline, or any MCP client can call them directly — without the LangGraph
runtime in the loop.

[Model Context Protocol]: https://modelcontextprotocol.io

## What is exposed

Nine tools, with schemas introspected from the LangChain `args_schema`
(Pydantic) so they stay in lock-step with the agent:

| Tool | Purpose |
|---|---|
| `assess_level` | Classify learner level (beginner / intermediate / advanced) on a subject. |
| `generate_exercise` | Structured math-for-ML exercise at the requested level. |
| `explain_concept` | Formal definition + real-world analogy. |
| `find_resources` | Curated textbooks, courses, videos. |
| `search_knowledge_base` | Hybrid BM25+dense retrieval over the Arquimedes Chroma corpus. |
| `solve_symbolic` | SymPy-powered derivative / integral / limit / solve / simplify / evaluate. |
| `plot_function` | Matplotlib PNG data URI for a 1-D function plot. |
| `step_by_step_derive` | Planner → step → verifier subgraph for multi-step proofs. |
| `solve_with_finetuned` | Routes to a LoRA-fine-tuned GSM8K solver (local GPU / HF Inference API). |

## Running the server

### Stdio (default — recommended for desktop clients)

```bash
cd /path/to/agents-demo
python -m arquimedes.mcp_server
```

### SSE (HTTP — multi-client demo / remote)

```bash
python -m arquimedes.mcp_server --sse --host 0.0.0.0 --port 8765
# → serves GET /sse and POST /messages/
```

Only stdout carries JSON-RPC frames; all logging goes to stderr so the
protocol channel stays clean.

## Connecting from Claude Desktop

Add a stanza to `~/Library/Application Support/Claude/claude_desktop_config.json`
(macOS) or `%APPDATA%/Claude/claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "arquimedes": {
      "command": "python",
      "args": ["-m", "arquimedes.mcp_server"],
      "cwd": "/absolute/path/to/agents-demo",
      "env": {
        "OPENAI_API_KEY": "${OPENAI_API_KEY}",
        "HF_TOKEN": "${HF_TOKEN}",
        "HF_FINETUNED_REPO": "${HF_FINETUNED_REPO}",
        "CHROMA_PATH": "/absolute/path/to/agents-demo/data/chroma"
      }
    }
  }
}
```

Restart Claude Desktop. The tools appear under the 🔌 icon.

## Connecting from Cursor

Add to `~/.cursor/mcp.json` (global) or `.cursor/mcp.json` (per-project):

```json
{
  "mcpServers": {
    "arquimedes": {
      "command": "python",
      "args": ["-m", "arquimedes.mcp_server"],
      "cwd": "/absolute/path/to/agents-demo"
    }
  }
}
```

## Connecting from Cline (VS Code)

In VS Code settings (workspace or user), add:

```json
{
  "cline.mcpServers": {
    "arquimedes": {
      "command": "python",
      "args": ["-m", "arquimedes.mcp_server"],
      "cwd": "/absolute/path/to/agents-demo"
    }
  }
}
```

## Debugging

- **"tool not found"** — the client caches tool lists; restart it.
- **stdio silent / hangs** — the server logs to stderr only. Run it
  directly (`python -m arquimedes.mcp_server`) and send a `tools/list`
  request by piping; or use `mcp-inspector`.
- **"unexpected non-JSON on stdout"** — some dependency (notably
  `sentence-transformers` first boot) writes progress bars to stdout.
  Set `TRANSFORMERS_VERBOSITY=error` or redirect via `PYTHONUNBUFFERED=1`.
- **RAG tool returns "unavailable"** — `CHROMA_PATH` env var isn't set
  to the ingested collection; copy the one from the API `.env`.

## Security

- The `solve_with_finetuned` tool calls HF Inference API with your
  `HF_TOKEN` if present. Revoke or rotate the token if you suspect leak.
- The SSE transport is unauthenticated by default — put it behind a
  reverse proxy with HTTP basic auth or `mtls` before exposing to the
  public internet.

## Relationship to the LangGraph agent

```
┌──────────── Shared ─────────────┐
│ arquimedes/tools/*              │
│  (@tool-decorated functions)    │
└────────┬──────────────┬─────────┘
         │              │
         ▼              ▼
┌────────────────┐  ┌────────────────────┐
│ LangGraph      │  │ MCP server         │
│ ToolNode       │  │ stdio / SSE        │
│ (in-process)   │  │ (cross-process)    │
└────────────────┘  └────────────────────┘
         ↓                  ↓
     your app          any MCP client
```

Zero code duplication: add a new tool once, both surfaces pick it up.
