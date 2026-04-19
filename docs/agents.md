# Agents

Three specialized LangGraph agents, each compiled into its own graph and
exposed under `/chat/{agent_name}` on the FastAPI server.

## Quick comparison

| Agent | Role | Tools | Memory | Graph nodes |
|---|---|---|---|---|
| **Prometheus** | AI compliance (GDPR, CCPA, EU AI Act, NIST AI RMF) | `regulations`, `penalties`, `risk_assessment`, `checklist`, `compare_jurisdictions` | Profile (compliance maturity, jurisdiction, AI systems) + summarization | 4 (assistant, tools, write_memory, summarize_conversation) |
| **Arquimedes** | Adaptive AI tutor (ML, Python, deep learning, LLM agents) | `assess_level`, `generate_exercise`, `explain_concept`, `recommend_resources` | Student profile (level, gaps, preferences) + summarization | 5 (assistant, tools, write_memory, summarize, route_by_level) |
| **Atlas** | Tech stack consultant (GitHub + HuggingFace) | `github_list_repos`, `github_repo_info`, `hf_search_models`, `analyze_project` | None (stateless tool-call loop) | 3 (assistant, tools, format_response) |

## Prometheus — AI Governance

**File**: `prometheus/agent.py`

ReAct loop with two extras:
1. **Long-term memory** — after each turn, `write_memory` extracts
   organization-level facts (industry, jurisdiction, AI systems,
   compliance maturity) and persists to `Store` under
   `("compliance_profile", user_id)`. On the next turn, those facts are
   prepended to the system prompt.
2. **Auto-summarization** — when message history exceeds 10 messages,
   `summarize_conversation` compresses everything into a `summary`
   string and emits `RemoveMessage` for old turns, keeping only the
   last 2.

**Use cases**:
- "What are the GDPR penalties for a data breach?"
- "Assess the EU AI Act risk level for a hiring screening AI."
- "Generate a GDPR compliance checklist."

## Arquimedes — Adaptive Tutor

**File**: `arquimedes/agent.py`

Same ReAct + memory + summarization pattern as Prometheus, with two
domain-specific differences:
- The memory namespace is `("student_profile", user_id)` and tracks
  prior knowledge level (beginner/intermediate/advanced), topics
  covered, gaps detected.
- A `route_by_level` conditional node selects between simple/technical
  explanation tools based on the persisted level.

**Use cases**:
- "I want to learn machine learning from scratch."
- "Explain transformers with a simple analogy."
- "Generate an intermediate exercise on gradient descent."

## Atlas — Stack Specialist

**File**: `atlas/agent.py`

Pure stateless ReAct loop — no profile memory, no summarization.
Tools call live external APIs:
- `github_list_repos`, `github_repo_info` → GitHub REST API (requires
  `GITHUB_TOKEN`)
- `hf_search_models` → HuggingFace Hub API (requires `HF_TOKEN`)
- `analyze_project` → fetches a repo's README + tech files and produces
  a structured stack summary

**Use cases**:
- "List all my GitHub repositories."
- "What's in my youtube_summarizer project?"
- "Recommend a technology for deploying an ML model as an API."

## Adding a new agent

1. Create `myagent/` with `agent.py`, `tools.py`, `prompts.py`
2. Build a `StateGraph` (use Prometheus as template if you need memory,
   Atlas if stateless)
3. Compile with `checkpointer=get_checkpointer(), store=get_store()`
4. Import the compiled `graph` in `api.py` and register in `AGENTS`
5. Add a tab in `ui.py` (Gradio) or rely on the React frontend reading
   `/agents` for dynamic registration
