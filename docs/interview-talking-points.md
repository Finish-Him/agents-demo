# Arquimedes — Interview Talking Points

> One-page reference for the AmBev pitch. For each concept: pitch line,
> file:line pointer, likely interview questions, trade-off to volunteer.

## 1 · LangChain (LCEL + Pydantic)

**Pitch**: the assistant uses `ChatPromptTemplate | llm.bind_tools(all_tools)`
so it's a composable Runnable — streams, batches, or traces without any
custom glue. Structured memory extraction uses `with_structured_output`
on a Pydantic model (`StudentProfileUpdate`) so we never parse free-form
strings.

**Code**: `arquimedes/chains.py:28-36` (assistant chain),
`arquimedes/schemas.py:18-35` (Pydantic models).

**Likely questions**
- *Why LCEL over classic Chains?* — Composability, async/batch for free,
  cleaner tracing in LangSmith.
- *Why Pydantic for memory?* — Typed validation; structured output
  protects against the model hallucinating a schema.

**Trade-off to volunteer**: some providers (e.g. HF Inference) don't
support reliable structured output — we gracefully fall back to a plain
LLM call in `arquimedes/agent.py:write_memory`.

## 2 · LangGraph (ReAct + router + subgraph)

**Pitch**: StateGraph with an entry router, a `rag_retrieve` node, a
ToolNode, summarisation, and a compiled subgraph for derivations — not a
linear agent, a *topology*.

**Code**: `arquimedes/agent.py:127-156` (graph assembly),
`arquimedes/subgraphs/derivation.py:62-72` (plan → step → verify subgraph),
`arquimedes/routing.py:44-52` (heuristic entry router).

**Likely questions**
- *Why a graph instead of a single prompt?* — Control flow, durable state
  (checkpointer), explicit error boundaries, testability per-node.
- *Why add a subgraph?* — Isolates a multi-step proof from the main
  conversation state. Each step/verify failure is retryable without
  leaking intermediate state.

**Trade-off**: we used a cheap heuristic router instead of an LCEL
classifier to save a model call per turn; when precision matters we can
flip to `build_router_chain()` (already in `arquimedes/chains.py:49-54`).

## 3 · RAG (ChromaDB + hybrid search)

**Pitch**: hybrid BM25 + dense (`langchain_chroma` + `rank_bm25`) with
Reciprocal Rank Fusion and optional cross-encoder rerank. Math prose is
symbol-heavy (∇, λ) where BM25 wins; concepts benefit from dense.

**Code**: `arquimedes/rag/retrieval.py:61-79` (RRF merge),
`arquimedes/rag/vector_store.py` (singleton).

**Likely questions**
- *Why Chroma and not Pinecone / Weaviate / FAISS?* — local-first, zero
  ops, survives restarts, LangChain first-class. Pinecone is the answer
  at cloud scale.
- *How do you avoid the "384-dim collection vs 1536-dim query" trap?* —
  `ingest.py` loads `.env` so the CLI picks the same embedding model as
  the API; future enhancement stamps the model name in metadata.

**Trade-off**: BM25 is rebuilt per query because the corpus is small.
Productionising means a persistent inverted index (OpenSearch) or moving
to pgvector with built-in tsvector.

## 4 · Chunks (LaTeX-aware + hierarchical)

**Pitch**: naïve character chunking cuts formulas in half. We match
`$...$`, `$$...$$`, and `\begin{equation}` blocks first, then delegate
prose to `RecursiveCharacterTextSplitter`. A hierarchical parent/child
mode is available for parent-expansion retrieval.

**Code**: `arquimedes/rag/chunking.py:33-45` (LaTeX split),
`arquimedes/rag/chunking.py:89-107` (hierarchical).

**Likely questions**
- *How did you pick 800/120?* — Empirical P@1 on a 30-query benchmark
  (see `docs/arquimedes-rag.md`); 800/120 won over 400/40 and 1500/150.
- *Why not semantic chunking?* — Expensive to ingest, marginal gains on
  well-structured textbook prose; we revisit if P@1 plateaus.

**Trade-off**: hierarchical chunking doubles index size (parent + child).
Worth it for symbol-heavy corpora; overkill for short FAQs.

## 5 · Fine-tuning (QLoRA on GSM8K)

**Pitch**: 4-bit QLoRA (`r=16`, `alpha=32`, attention-only target
modules) on Qwen2.5-1.5B-Instruct, 1 epoch × 5 000 GSM8K examples. Fits
on a T4 in ~2 h; pushed to HF Hub; runtime loader has three paths
(local GPU → Inference API → honest fallback).

**Code**: `arquimedes/finetuning/train_lora.ipynb`,
`arquimedes/finetuning/config.yaml`,
`arquimedes/tools/finetuned_solver.py:54-94` (three-tier runtime).

**Likely questions**
- *Full FT vs. LoRA vs. QLoRA — why QLoRA?* — VRAM. 1.5B full FT needs
  ~24 GB; QLoRA runs on a T4 (16 GB).
- *How do you evaluate?* — `eval.py` greedy-decodes GSM8K test, regex-
  extracts `#### <number>`, reports exact-match accuracy base vs.
  adapter.
- *What if training fails the night before the demo?* — The tool
  accepts any HF adapter — point it at a public MAmmoTH LoRA. Risk
  documented in `finetuning/README.md`.

**Trade-off**: QLoRA's quantisation can cost 1–2 pp accuracy vs.
BF16 LoRA. We accepted it for the VRAM saving.

## 6 · Tools (9 decorated functions)

**Pitch**: every capability is a `@tool`-decorated Python function:
teaching, textbook retrieval, SymPy, matplotlib, fine-tuned solver,
derivation subgraph. One list (`all_tools`) feeds both LangGraph
ToolNode and the MCP server, so adding a tool is a one-file change.

**Code**: `arquimedes/tools/__init__.py:38-46` (registry).

**Likely questions**
- *How do you prevent the agent from picking the wrong tool?* — Clear,
  narrow docstrings (the LLM picks from them), strict Pydantic schemas,
  and prompt-level guidance in `arquimedes/prompts.py`.
- *How do you handle tool failures?* — Each tool catches and returns a
  prefixed error string; the agent's next turn sees it and can recover.

**Trade-off**: too many tools widens the selection distribution and
hurts latency. We capped at 9 and considered grouping (teaching-vs-
solving) if it grows further.

## 7 · MCP (Model Context Protocol)

**Pitch**: `python -m arquimedes.mcp_server` — same 9 tools, now
consumable by Claude Desktop / Cursor / Cline. Schemas are introspected
from the LangChain `args_schema`, so parity with the in-process agent is
enforced by construction.

**Code**: `arquimedes/mcp_server/server.py:54-81`,
`docs/arquimedes-mcp.md` for client configs.

**Likely questions**
- *MCP vs. LangChain tools — which is the "real" interface?* — Both.
  LangChain is in-process, latency-optimised; MCP is cross-process,
  cross-vendor. We ship both because they serve different consumers.
- *Why introspect instead of writing schemas twice?* — Drift kills. One
  source of truth.

**Trade-off**: MCP's stdio transport makes debugging ugly (all logs to
stderr or they corrupt JSON-RPC). We document that and provide the SSE
fallback for inspection.

## 8 · HuggingFace (three integration points)

**Pitch**: HF is everywhere — `hf/<repo>` prefix in the LLM factory
(Inference API), `sentence-transformers` embedding fallback, LoRA
adapter push/pull for fine-tuning. No vendor lock-in.

**Code**: `shared/llm.py:96-114` (Inference API branch),
`arquimedes/rag/embeddings.py`,
`arquimedes/tools/finetuned_solver.py`.

**Likely questions**
- *Why HF Inference API and not a dedicated endpoint?* — Zero ops, pay
  per call, ideal for a demo VPS; the same code works with dedicated
  endpoints by changing the base URL.
- *Local model vs. API — when do you use which?* — Local for high
  throughput / data residency; API for bursty / low-volume demos.

**Trade-off**: Inference API cold-starts the model on first hit (up to
30 s). We warn about it in the docs; dedicated endpoints remove this.

## 9 · Memory (two tiers + semantic)

**Pitch**: two layers — a **checkpointer** for thread history and a
**Store** for cross-session learner facts. The Store is Chroma-backed,
so retrieval is *semantic* similarity, not prefix-scan.

**Code**: `shared/memory.py` (backend selection),
`shared/semantic_store.py` (Chroma wrapper implementing the
BaseStore-compatible surface),
`arquimedes/agent.py:51-62` (semantic profile retrieval).

**Likely questions**
- *Why semantic and not prefix?* — Prefix-scan dumps every fact into
  the system prompt (token cost, context pollution). Semantic retrieves
  only facts relevant to the current turn.
- *MemorySaver / SqliteSaver / AsyncSqliteSaver — how do you pick?* —
  Event-loop detection at call time (`shared/memory.py:60-78`). Dev
  stays on MemorySaver; prod flips via `SQLITE_CHECKPOINT_PATH` or
  moves to PostgresSaver + Supabase.

**Trade-off**: semantic search has an embedding cost per turn. Capped
at `limit=5` to bound latency; future work is to cache by user.

---

## Closing lines

- **"Why should I hire you?"** — I built a working agent that teaches
  the same concepts AmBev's AI team is adopting. Every box on the job
  description (LLMs, agent architecture, RAG, vector DBs, REST APIs, Git,
  Postgres) is green in the repo, with tests.
- **"What would you do on day 1?"** — Stand up the same stack against
  an AmBev knowledge base — start with one team's docs, measure P@1,
  iterate on chunking and the router. Then expose the tools over MCP so
  the rest of the org can plug in without waiting on me.
