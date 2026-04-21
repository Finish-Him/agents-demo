# Arquimedes — Math-for-ML Tutor

> An adaptive AI tutor that teaches the math under machine learning — linear
> algebra, calculus, probability, statistics — and demonstrates, in a single
> codebase, nine production techniques every AI Engineer needs: **LangChain,
> LangGraph, RAG, Chunks, Fine-tuning, Tools, MCP, HuggingFace, Memory**.

## Persona

- **Name**: Archimedes.
- **Primary domain**: math-for-ML (linear algebra, calculus, probability,
  statistics).
- **Secondary breadth**: ML, deep learning, Python, LLM agents.
- **Voice**: Socratic — assesses first, explains with analogy **plus**
  formal definition, always shows intermediate steps, celebrates progress,
  corrects gently.
- **LaTeX-first**: every formula ships in `$...$` or `$$...$$` so the React
  frontend renders it via KaTeX.

## Architecture

```
                       ┌────────────────────┐
START ── entry_route ──▶  rag_retrieve       │── factual / citation-seeking
   │                   │  (hybrid BM25+dense)│
   │                   └──────────┬─────────┘
   │                              ▼
   └────────────────────▶  assistant (LCEL: prompt | llm.bind_tools)
                                  │
                       tools_condition
                      ┌───────────┴────────────┐
                      ▼                        ▼
                 ToolNode(all_tools)      write_memory
                      │                        │ should_continue
                      │                        ▼
                      └───▶ assistant     summarize_conversation
                                                ▼
                                               END

subgraph derivation: plan → step → verifier (invoked via step_by_step_derive tool)
```

### Nine concepts mapped to code

| # | Concept | Where it lives | Notes |
|---|---|---|---|
| 1 | **LangChain** | `arquimedes/chains.py` | LCEL runnables, `ChatPromptTemplate | llm.bind_tools`, structured output via Pydantic (`with_structured_output`). |
| 2 | **LangGraph** | `arquimedes/agent.py`, `arquimedes/subgraphs/derivation.py` | StateGraph with conditional edges, ToolNode, entry router, compiled subgraph for derivations. |
| 3 | **RAG** | `arquimedes/rag/` | ChromaDB (persistent), hybrid BM25 + dense retrieval with Reciprocal Rank Fusion, optional cross-encoder rerank. |
| 4 | **Chunks** | `arquimedes/rag/chunking.py` | LaTeX-aware splitter (preserves `$$...$$`), hierarchical parent/child, RecursiveCharacterTextSplitter. |
| 5 | **Fine-tuning** | `arquimedes/finetuning/` | QLoRA on Qwen2.5-1.5B over GSM8K; `train_lora.ipynb` + `eval.py` + `solve_with_finetuned` runtime loader. |
| 6 | **Tools** | `arquimedes/tools/` | 9 `@tool`-decorated functions: teaching, RAG, symbolic (SymPy), plotting (matplotlib), derivation subgraph wrapper, fine-tuned solver. |
| 7 | **MCP** | `arquimedes/mcp_server/` | Stdio + SSE. Introspects `args_schema` from every tool → schema parity with the LangGraph agent. |
| 8 | **HuggingFace** | `shared/llm.py`, `arquimedes/rag/embeddings.py`, `arquimedes/finetuning/` | `hf/<repo>` model prefix (Inference API), MiniLM embeddings fallback, LoRA adapter push/pull. |
| 9 | **Memory** | `shared/memory.py`, `shared/semantic_store.py`, `arquimedes/agent.py` | AsyncSqliteSaver / MemorySaver checkpointer + Chroma-backed **semantic** store (similarity search of student facts). |

## Component diagram

```
┌──────────────────────── React (Vite + Tailwind + Zustand) ────────────────────────┐
│ ChatMessage renders Markdown + KaTeX (remark-math + rehype-katex) + code blocks   │
│ ToolTrace shows one chip per tool call with name, icon, color, duration            │
│ SSE parser (buffer-safe) dispatches metadata / token / tool_start / tool_end       │
└────────────────────────────────────┬──────────────────────────────────────────────┘
                                     │  SSE
┌────────────────────────────────────▼──────────────────────────────────────────────┐
│ FastAPI  (api.py)                                                                 │
│  /health  /agents  /models  /chat/{name}  /chat/{name}/stream                     │
│  stream: graph.astream_events(v2) + filter by langgraph_node == 'assistant'       │
└────────────────────────────────────┬──────────────────────────────────────────────┘
                                     │
                                     ▼
┌──────────────────────── LangGraph compiled graph ─────────────────────────┐
│ entry_route → rag_retrieve? → assistant ↔ ToolNode(all_tools)             │
│ → write_memory → should_continue → summarize_conversation                 │
│ State extends MessagesState with {summary, retrieved_context}              │
└───────────┬──────────────┬───────────────┬───────────────────────────────┘
            │              │               │
            ▼              ▼               ▼
     ChromaDB (RAG)   LLM factory   Memory (checkpointer + SemanticStore)
      hybrid BM25     OpenRouter    MemorySaver / AsyncSqliteSaver +
      + dense         OpenAI        Chroma-backed vector store
      + rerank        Anthropic
                      Google
                      Azure
                      HuggingFace

┌──────────────── MCP server (separate process) ────────────────┐
│ python -m arquimedes.mcp_server [--sse --port 8765]            │
│ Exposes the same 9 @tool functions to Claude Desktop / Cursor  │
└───────────────────────────────────────────────────────────────┘
```

## Data flow for a typical query

1. Student asks *"Derive the gradient of MSE and cite the textbook."*
2. `entry_route` sees "cite" + "textbook" → routes to `rag_retrieve`.
3. `rag_retrieve` runs hybrid BM25 + dense over Chroma, picks top-4
   passages, stores them in `state.retrieved_context`.
4. `assistant` builds its system prompt = `SYSTEM_PROMPT` + student
   profile (semantic-search over Store) + conversation summary +
   retrieved passages. Sends through the LCEL chain.
5. LLM chooses `solve_symbolic` to verify the derivative. ToolNode runs
   SymPy; result streams back.
6. Assistant composes the final answer with LaTeX formulas + textbook
   citation. `tools_condition` = `__end__` → goes to `write_memory`.
7. `write_memory` invokes a structured extractor (`StudentProfileUpdate`
   Pydantic schema); each fact is upserted into the SemanticStore so
   next session's `assistant` node can retrieve it by similarity.
8. `should_continue` → `summarize_conversation` if history > 10 msgs,
   else END.

## Trade-offs worth discussing in interviews

1. **Vector store**: Chroma (local-first, zero ops) vs. Pinecone (cloud
   scale) vs. FAISS (low-level) vs. Weaviate (heavier). See
   `docs/arquimedes-rag.md`.
2. **Checkpointer**: MemorySaver (dev) vs. SqliteSaver (sync-only) vs.
   AsyncSqliteSaver (requires a running loop) vs. PostgresSaver
   (production). Event-loop detection in `shared/memory.py`.
3. **Embeddings**: OpenAI `text-embedding-3-small` (1536d, paid) vs.
   `sentence-transformers/all-MiniLM-L6-v2` (384d, local). Auto-fallback
   in `arquimedes/rag/embeddings.py`.
4. **Chunking**: fixed-size vs. recursive vs. LaTeX-aware vs. hierarchical.
   See the empirical table in `docs/arquimedes-rag.md`.
5. **Fine-tuning**: full FT vs. LoRA vs. QLoRA. We pick QLoRA (4-bit NF4)
   to fit on a T4.
6. **Retrieval**: dense-only vs. sparse-only vs. hybrid. Math prose has
   lots of exact symbol tokens (∇, λ) where BM25 wins; concepts benefit
   from dense. Hybrid + optional cross-encoder rerank.
7. **MCP vs. LangChain tools**: in-process vs. cross-process. We expose
   the same `@tool` objects on both surfaces so adding a new tool once
   updates both.

## How to run locally

```bash
# 0. setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in keys

# 1. ingest the corpus
python -m arquimedes.rag.ingest --reset

# 2. start the API (serves the React build + REST + SSE)
python api.py
# → http://localhost:8000

# 3. (optional) LangGraph Studio for visual debugging
langgraph dev

# 4. (optional) MCP server for Claude Desktop / Cursor / Cline
python -m arquimedes.mcp_server
# see docs/arquimedes-mcp.md for client config
```

## How to deploy

- Docker Compose is already wired (`docker-compose.yml`); `docker compose
  up -d --build` on the VPS picks up the branch.
- `.github/workflows/deploy.yml` handles SSH deploy on push to `main`.
- Production checklist:
  - set LangSmith env vars so traces are captured.
  - point `CHROMA_PATH` at a mounted volume to survive restarts.
  - swap MemorySaver → AsyncSqliteSaver (set `SQLITE_CHECKPOINT_PATH` and
    ensure the uvicorn loop is live on first call) or PostgresSaver.
  - put the SSE MCP endpoint behind a reverse proxy with auth.

## See also

- `docs/arquimedes-rag.md` — corpus manifest, chunking, retrieval eval.
- `docs/arquimedes-finetuning.md` (at `arquimedes/finetuning/README.md`)
  — dataset, hyperparameters, inference modes.
- `docs/arquimedes-mcp.md` — MCP server setup for Claude Desktop / Cursor / Cline.
- `docs/interview-talking-points.md` — pitch lines + likely questions.
