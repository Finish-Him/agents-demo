# 🤖 Agentes

Três agentes LangGraph especializados, cada um compilado em seu próprio
graph e exposto sob `/chat/{agent_name}` no servidor FastAPI.

> 💡 Para o **deep-dive** do Arquimedes (o agente em destaque para a entrevista),
> veja [`arquimedes.md`](./arquimedes.md).

## 🔍 Comparação rápida

| Agente | Papel | Tools | Memória | Nós do graph |
|---|---|---|---|---|
| 🛡️ **Prometheus** | Compliance de IA (GDPR, CCPA, EU AI Act, NIST AI RMF) | `regulations`, `penalties`, `risk_assessment`, `checklist`, `compare_jurisdictions` | Perfil de compliance + sumarização | 4: `assistant`, `tools`, `write_memory`, `summarize_conversation` |
| 🎓 **Arquimedes** | Tutor de matemática para ML (álgebra linear, cálculo, probabilidade, estatística) | **9 tools** — ensino, RAG, SymPy, plot, derivação, fine-tuned solver | Perfil do aluno (semântico) + sumarização + RAG retrieve | 5: `rag_retrieve`, `assistant`, `tools`, `write_memory`, `summarize_conversation` |
| 🗺️ **Atlas** | Consultor de stack (GitHub + HuggingFace) | `github_list_repos`, `github_repo_info`, `hf_search_models`, `analyze_project` | Stateless | 3: `assistant`, `tools`, `format_response` |

---

## 🛡️ Prometheus — AI Governance

📂 `prometheus/agent.py`

ReAct loop com dois extras:

- 🧠 **Memória de longo prazo** — após cada turno, `write_memory` extrai
  fatos organizacionais (indústria, jurisdição, sistemas de IA, maturidade
  de compliance) e persiste no `Store` sob `("compliance_profile", user_id)`.
- ✂️ **Auto-sumarização** — ao passar de 10 mensagens,
  `summarize_conversation` comprime o histórico em um `summary`,
  preservando apenas as 2 últimas mensagens.

**Casos de uso:**
- "Quais são as multas da GDPR para vazamento de dados?"
- "Avalie o risco da EU AI Act para uma IA de triagem de currículos."
- "Gere um checklist de conformidade GDPR."

---

## 🎓 Arquimedes — Tutor de Matemática para ML

📂 `arquimedes/agent.py` · 📖 [`arquimedes.md`](./arquimedes.md) (deep-dive)

Topologia LangGraph mais rica que Prometheus — adiciona:

- 🔀 **Router de entrada** (`arquimedes/routing.py`) — heurística de
  citation-seeking direciona para `rag_retrieve` antes do `assistant`.
- 🔎 **Nó `rag_retrieve`** — busca híbrida BM25 + densa em ChromaDB
  (`arquimedes/rag/retrieval.py`) e injeta as passagens encontradas no
  system prompt.
- 🧮 **Subgraph de derivação** — `arquimedes/subgraphs/derivation.py`
  com nós `plan` → `step` → `verify`, exposto via tool
  `step_by_step_derive`.
- 🧠 **Memória semântica** — `shared/semantic_store.py` (Chroma) ou
  `shared/postgres_store.py` (pgvector / Supabase) recupera fatos do
  aluno por similaridade (não por prefix-scan).

**Casos de uso:**
- "Explique autovetores com uma analogia geométrica e cite o livro-texto."
- "Derive passo a passo o gradiente da função de perda MSE."
- "Exercício intermediário de Teorema de Bayes — depois corrija minha resposta."

---

## 🗺️ Atlas — Stack Specialist

📂 `atlas/agent.py`

Loop ReAct puro stateless — sem memória de perfil, sem sumarização.
Tools fazem chamadas a APIs externas:

- `github_list_repos`, `github_repo_info` → GitHub REST API (requer `GITHUB_TOKEN`)
- `hf_search_models` → HuggingFace Hub API (requer `HF_TOKEN`)
- `analyze_project` → busca README + arquivos técnicos do repo e produz um resumo estruturado da stack

**Casos de uso:**
- "Liste meus repositórios do GitHub."
- "O que tem no meu projeto youtube_summarizer?"
- "Recomende uma stack para expor um modelo de ML como API."

---

## ➕ Adicionando um novo agente

1. Crie `meu_agente/` com `agent.py`, `tools.py`, `prompts.py`.
2. Construa um `StateGraph` — use **Prometheus** como template se precisar
   de memória, **Atlas** se for stateless, **Arquimedes** se for usar RAG
   + LCEL + subgraph.
3. Compile com `checkpointer=get_checkpointer(), store=get_store()`.
4. Importe o `graph` compilado em `api.py` e registre no dict `AGENTS`.
5. (Opcional) adicione uma aba em `ui.py` (Gradio) ou apenas confie no
   frontend React que lê `/agents` dinamicamente.
