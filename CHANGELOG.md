# 📜 Changelog

Formato: [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) ·
Versionamento: [SemVer](https://semver.org/lang/pt-BR/).

## [Unreleased] — branch `claude/arquimedes-math-agent-Mj90C`

### ✨ Adicionado
- **Identidade visual Mouts × AmBev** — banner de marca, hero PT-BR
  com SVG da alavanca de Arquimedes, footer com atribuição, paleta
  Tailwind com tokens `mouts` (verde) + `ambev` (dourado) +
  `accent` (indigo).
- **framer-motion** com fades, slides, scale-pop em mensagens, modal
  de conceitos e tool trace.
- **Postgres + pgvector** (`shared/postgres_store.py`) como backend
  de produção para memória semântica (Supabase-ready).
- **Documentação completa** — `docs/arquimedes.md`,
  `docs/arquimedes-rag.md`, `docs/arquimedes-mcp.md`,
  `docs/observability.md`, `docs/interview-talking-points.md`.
- **CHANGELOG.md**, **CONTRIBUTING.md**, **TODO.md**, **LICENSE** raiz.
- **Workflow de deploy auto-bootstrapping** —
  `.github/workflows/deploy.yml` faz SSH ao VPS sozinho via runner do
  Actions (resolve o gargalo de SSH bloqueado em sandboxes).
- **MCP server** (`arquimedes/mcp_server/`) expondo as 9 tools via
  stdio/SSE para Claude Desktop, Cursor, Cline.
- **Fine-tuning pipeline** — notebook QLoRA Colab + eval GSM8K +
  `solve_with_finetuned` tool com 3 modos de runtime.
- **RAG híbrido** — ChromaDB + BM25 + denso com Reciprocal Rank Fusion
  e chunker LaTeX-aware.
- **Subgraph de derivação** — plan → step → verify exposto via
  `step_by_step_derive`.
- **9 tools matemáticas** — teaching, RAG, SymPy, plot, derivação,
  fine-tuned solver.
- **Memória semântica** — busca por similaridade no perfil do aluno.
- **LCEL chains + Pydantic schemas** — saída tipada do extrator de
  memória (`StudentProfileUpdate`).
- **Modal "Como funciona"** com 9 cards traduzidos e exemplos clicáveis.

### 🔄 Modificado
- Persona Arquimedes refocada de "tutor genérico" para
  **matemática para ML** (álgebra linear, cálculo, probabilidade,
  estatística como primários; ML/Python/DL como secundários).
- Copy 100% PT-BR no UI (Sidebar, ChatInput, ConceptsPanel, Hero,
  Footer, `index.html`, `api.py`).
- Grafia padronizada **Arquimedes** (PT) em todo o repo (antes
  alternava entre "Archimedes"/"Arquimedes").
- `StoreRecord` extraído para `shared/store_types.py` (DRY entre
  Chroma e Postgres backends).

### 🐛 Corrigido
- Stream SSE: tokens de `write_memory` e `summarize_conversation`
  vazavam para o usuário ("No new information"). Agora filtramos
  por `langgraph_node == 'assistant'`.
- `write_memory` enviava `ToolMessage` órfão para providers que
  validam pareamento `tool_calls`/`tool_result` — agora filtramos
  tipos de mensagem antes do extrator.
- Parser SSE no frontend (`lib/api.ts`) era frágil (usava
  `lines.indexOf`); reescrito para split por blank-lines e dispatch
  por nome de evento.
- `AsyncSqliteSaver` exigia event loop ativo no construtor — agora
  detectamos em runtime e caímos para `MemorySaver` se não houver loop.
- `data/`, `*.tsbuildinfo` e `frontend/test-results/` removidos do
  versionamento.

### 🗑️ Removido
- Atribuição "Built by Moises Alves for Factored.ai" — substituída
  por "construído para Mouts IT × AmBev".
- Menção a `route_by_level` em `docs/agents.md` (nó nunca foi
  implementado).
