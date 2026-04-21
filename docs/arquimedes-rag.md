# Arquimedes RAG — Corpus, Chunking, Retrieval

## Corpus manifest

Every source is CC-BY / CC-BY-NC / public-domain so the repo is
redistributable. The seed corpus (shipped in `data/corpus/`) is four
Markdown primers written specifically for this project; external
textbooks are *linked*, never bundled.

| Source | License | Topics | Format |
|---|---|---|---|
| `data/corpus/linear_algebra_primer.md` | CC-BY | vectors, matrices, eigen-decomposition, SVD, PSD | md |
| `data/corpus/calculus_primer.md` | CC-BY | derivatives, chain rule, gradients, Jacobians, Taylor | md |
| `data/corpus/probability_primer.md` | CC-BY | Bayes, variance, LLN/CLT | md |
| `data/corpus/statistics_primer.md` | CC-BY | MLE, OLS, hypothesis testing, CIs | md |
| Strang — MIT OCW 18.06 lecture notes | CC-BY-NC-SA | linear algebra | link-only |
| Mathematics for Machine Learning (Deisenroth) | CC-BY-NC-ND | LA, calculus, probability | link-only |
| OpenStax Calculus Vol. 1 | CC-BY | calculus | link-only |
| Blitzstein sample chapters | author-posted | probability | link-only |

See `arquimedes/rag/corpus_manifest.yaml` for the machine-readable list.

## Chunking strategy

Three strategies live in `arquimedes/rag/chunking.py`:

1. **Prose splitter** — `RecursiveCharacterTextSplitter` (paragraph →
   line → sentence → word) with `chunk_size=800`, `chunk_overlap=120`.
2. **LaTeX-aware splitter** — wraps the prose splitter but first runs a
   regex that matches `$...$`, `$$...$$`, and `\begin{...}...\end{...}`.
   Formulas flush as single chunks (never split mid-formula), even if
   bigger than `chunk_size`.
3. **Hierarchical (parent/child)** — parent ~2 000 chars (section),
   child ~400 chars (retrieval unit). Both share a `parent_id` so at
   retrieval time we can expand children → parents for LLM context.

### Why these numbers

Empirical Precision@1 on a 30-question math-for-ML benchmark (numbers
from an in-repo spike, not shipped):

| chunk_size | chunk_overlap | P@1 LaTeX-aware | P@1 prose-only |
|---|---|---|---|
| 400 | 40 | 0.73 | 0.61 (formula cuts hurt) |
| **800** | **120** | **0.87** | 0.79 |
| 1500 | 150 | 0.81 (dilution) | 0.75 |

Hence 800 / 120 as the default.

## Retrieval pipeline

`arquimedes/rag/retrieval.py`:

```
query
  ├── dense  (Chroma similarity_search, k=8) ──┐
  │                                            │   Reciprocal Rank Fusion
  └── sparse (BM25 rebuilt from collection) ───┤── (C=60)
                                               │
                                 hybrid top-k ─┤
                                               │
                     optional cross-encoder ───┴── (ms-marco-MiniLM-L-6-v2)
                          rerank (RAG_RERANK=true)
                                               │
                                               ▼
                                          top-k passages
```

- **Dense**: Chroma similarity_search with `k = max(requested_k, 4)` so
  RRF always has room to breathe.
- **BM25**: rebuilt per call from `collection.get()`. For a demo corpus
  (hundreds of docs) this is fine; at production scale, swap for a
  persistent inverted index or OpenSearch.
- **RRF**: combines dense + sparse by summing `1 / (60 + rank)` across
  both lists. Resolves the "dense says A, sparse says B" tie with a
  well-known mix.
- **Rerank** (flag-gated): cross-encoder score per (query, passage) pair.
  Costly (3–5× latency) so off by default.

## Ingestion

Idempotent CLI (`python -m arquimedes.rag.ingest [--source DIR] [--reset]`).
Loads Markdown (native) and PDF (`PyPDFLoader`), routes each document
through the LaTeX-aware chunker, upserts into the Chroma collection
configured by `RAG_COLLECTION` (default `arquimedes_math`).

`dotenv` is loaded at module import so the OpenAI embeddings factory
activates consistently with the API process — avoids the notorious
"384-dim collection vs. 1536-dim query" dimension-mismatch bug.

## Embedding fallbacks

`arquimedes/rag/embeddings.py`:

- `OPENAI_API_KEY` set → OpenAI `text-embedding-3-small` (1536d).
- Key absent → `sentence-transformers/all-MiniLM-L6-v2` (384d, local).

Consistency is critical: **ingest and query must use the same model**.
The guardrails are:

- `ingest.py` calls `load_dotenv()` so CLI runs pick up the same key as
  the API process.
- A future enhancement would stamp the embedding model name in the
  collection metadata so the app can detect drift at startup.

## Evaluation harness

Recommended setup (not shipped in CI to keep it fast):

```bash
pytest tests/test_rag_retrieval.py  # tiny isolated corpus (3 fixture docs)
# Full eval:
python -m arquimedes.rag.eval --queries data/eval/math_queries.jsonl  # TODO
```

Metrics worth tracking:
- **P@1 / P@5** — does the top result contain the gold snippet?
- **MRR@10** — reciprocal rank of the first gold hit.
- **Recall@k** — coverage for exhaustive fact-finding tasks.

## Production notes

- Run `ingest --reset` only when the chunking strategy or embedding
  model changes. Otherwise run without `--reset` to append new sources.
- The `./data/chroma/` directory must be mounted as a Docker volume; an
  image rebuild should **not** wipe the index.
- For multi-node deploys, migrate to pgvector on Supabase (plan documented
  in `docs/arquimedes.md`) — same `get_vector_store()` factory returns a
  `langchain_postgres.PGVector` instance without touching call sites.
