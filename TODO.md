# 📋 TODO

> Status do projeto **Arquimedes — Mouts × AmBev** após auditoria completa.

---

## 🚀 Bloqueio para a entrevista

### 🔴 Crítico (necessário pra demo live)

- [ ] **Subir no VPS Hostinger** `187.77.37.158`. Duas opções:
  - **A. SSH manual** (5 min):
    ```bash
    ssh root@187.77.37.158
    curl -sLO https://raw.githubusercontent.com/Finish-Him/agents-demo/claude/arquimedes-math-agent-Mj90C/deploy/bootstrap.sh
    bash bootstrap.sh                           # cria .env e para
    nano /opt/agents-demo/.env                  # cole as chaves
    bash /opt/agents-demo/deploy/bootstrap.sh   # builda + sobe
    ```
  - **B. GitHub Actions** (zero terminal): adicionar 7 secrets no repo
    (`VPS_HOST`, `VPS_USER`, `VPS_PASSWORD`, `OPENROUTER_API_KEY`,
    `OPENAI_API_KEY`, `HF_TOKEN`, `LANGSMITH_API_KEY`) e disparar o
    workflow **Deploy** com a branch
    `claude/arquimedes-math-agent-Mj90C`.
- [ ] **Rotacionar chaves** após o deploy — as compartilhadas no chat
  ainda estão válidas e podem aparecer em screenshots/logs.

### 🟠 Alto valor (pra impressionar)

- [ ] **Treinar o LoRA real** em Colab T4 ou RunPod A10
  (`arquimedes/finetuning/train_lora.ipynb`). Publicar no HF Hub.
  Atualizar `HF_FINETUNED_REPO` no `.env`.
  - **Fallback** se o tempo apertar: apontar `HF_FINETUNED_REPO` para
    um adapter público pré-treinado (ex.: `TIGER-Lab/MAmmoTH`).
- [ ] **Rodar `eval.py`** comparando base vs adapter em GSM8K test e
  colar o número (acurácia exact-match) em
  `docs/interview-talking-points.md` (seção Fine-tuning).
- [ ] **Configurar Supabase** (criar projeto, executar a CREATE TABLE
  do `shared/postgres_store.py`, definir `POSTGRES_URL` no `.env`).
  Demonstra item da vaga: "PostgreSQL + Vector DBs (pgvector)".

---

## 🧹 Auditoria — concluído nesta rodada

| Severidade | Item | Status |
|---|---|---|
| 🔴 HIGH | Grafia "Arquimedes" (PT) padronizada em todo o repo | ✅ |
| 🔴 HIGH | Remover `route_by_level` inexistente de `docs/agents.md` | ✅ |
| 🔴 HIGH | `.gitignore` com `*.tsbuildinfo`, `frontend/test-results/`, `data/` + untrack dos artefatos vazados | ✅ |
| 🟡 MED | `StoreRecord` extraído para `shared/store_types.py` (DRY entre Chroma e Postgres) | ✅ |
| 🟡 MED | LICENSE (MIT) + CHANGELOG.md + CONTRIBUTING.md + TODO.md | ✅ |
| 🟡 MED | `docs/agents.md` reescrito com PT-BR + emojis + defere para `arquimedes.md` | ✅ |
| 🟡 MED | `prompts.py` migrado para PT-BR | ✅ |

---

## ⏭️ Pós-entrevista (tech debt)

### 🟡 Refactor

- [ ] Migrar `prometheus/agent.py` e `atlas/agent.py` para o padrão
  LCEL (`build_assistant_chain`) — hoje usam `llm.invoke` direto,
  divergindo do Arquimedes.
- [ ] Subir `BM25Retriever` para um índice persistente (OpenSearch ou
  pgvector tsvector) — hoje é reconstruído por query, ok pra demo
  mas não escala.
- [ ] Stamp do nome do modelo de embedding nos metadata da collection
  Chroma — evita a armadilha "384-dim collection vs 1536-dim query".
- [ ] Code-splitting no Vite (`manualChunks`) — bundle único hoje
  passa de 750 KB.

### 🟢 Nice to have

- [ ] **Toggle PT/EN** no UI (i18n) com biblioteca leve (`@formatjs/intl`).
- [ ] **Dashboard de sessão** — barra mostrando tokens consumidos,
  tools usadas, latência P95 (lê de LangSmith via SDK).
- [ ] **Export da conversa** (Markdown / PDF) com fórmulas KaTeX
  renderizadas.
- [ ] **Exercícios persistidos** — Postgres table de problemas
  resolvidos, com revisão espaçada (Anki-style).
- [ ] **`pre-commit` hooks** (ruff + black + mypy + prettier) —
  começa simples, evolui.
- [ ] **Auditoria de acessibilidade** — Playwright + axe-core;
  Modal de conceitos precisa de focus trap e ESC para fechar.
- [ ] **Cache de embeddings** por turno no `write_memory`.

### 🛡️ Segurança

- [ ] Reverse-proxy com auth para o MCP SSE (porta 8765) — hoje é
  open por padrão.
- [ ] Rate-limit em `/chat/{agent}/stream` — sem proteção contra
  abuso.
- [ ] Scrub de PII antes de upload pro LangSmith
  (`langchain.callbacks.tracers.langchain.LangChainTracer` aceita
  hooks).

---

## 📚 Documentação produzida

- 📖 `README.md` — visão geral + stack + quickstart
- 📖 `docs/arquimedes.md` — deep-dive da arquitetura
- 📖 `docs/arquimedes-rag.md` — corpus + chunking + retrieval
- 📖 `docs/arquimedes-mcp.md` — setup MCP em Claude Desktop / Cursor / Cline
- 📖 `docs/observability.md` — LangSmith + métricas
- 📖 `docs/interview-talking-points.md` — pitch por conceito
- 📖 `docs/agents.md` — comparação dos 3 agentes
- 📖 `docs/architecture.md` — diagrama do sistema
- 📖 `docs/api.md` — referência REST/SSE
- 📖 `arquimedes/finetuning/README.md` — pipeline de fine-tuning
- 📖 `deploy/README.md` — bootstrap do VPS
- 📖 `CHANGELOG.md` · `CONTRIBUTING.md` · `LICENSE` · `TODO.md`
