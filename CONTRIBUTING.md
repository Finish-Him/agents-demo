# 🤝 Contribuindo

Bem-vindo. Este é um repo de demonstração para entrevista técnica
**AI Engineer · Mouts IT × AmBev**, mas pull requests externos são
bem-vindos para correções de bugs e melhorias de documentação.

## 🧭 Onde começar

| Quero… | Vá para… |
|---|---|
| Entender a arquitetura | [`docs/arquimedes.md`](docs/arquimedes.md) |
| Entender o RAG | [`docs/arquimedes-rag.md`](docs/arquimedes-rag.md) |
| Conectar via MCP | [`docs/arquimedes-mcp.md`](docs/arquimedes-mcp.md) |
| Ver traces no LangSmith | [`docs/observability.md`](docs/observability.md) |
| Treinar a LoRA do zero | [`arquimedes/finetuning/README.md`](arquimedes/finetuning/README.md) |
| Subir no VPS | [`deploy/README.md`](deploy/README.md) |
| Roadmap pendente | [`TODO.md`](TODO.md) |

## 🛠️ Setup local

```bash
git clone https://github.com/Finish-Him/agents-demo.git
cd agents-demo
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # preencha as chaves
python -m arquimedes.rag.ingest --reset
python api.py          # http://localhost:8000
```

Frontend separado:
```bash
cd frontend && npm install && npm run dev
```

## ✅ Antes de abrir um PR

1. **Testes**: `python -m pytest tests/ -q` deve ficar verde (≥ 142 testes).
2. **Build do frontend**: `cd frontend && npm run build` deve compilar
   sem erros TS.
3. **Tipagem**: evite `any` no TypeScript; use Pydantic ou `BaseModel`
   no Python para entradas/saídas estruturadas.
4. **Naming**: `snake_case` em Python, `PascalCase` em componentes
   React, `kebab-case.spec.ts` em testes Playwright.
5. **Commits**: mensagens no formato
   `<scope>(<area>): <ação>` — ex.: `feat(arquimedes): adiciona X`,
   `fix(rag): corrige Y`, `docs(observability): atualiza Z`.
6. **PR**: explique o **porquê** no corpo, não só o quê. Se for um
   bug fix, descreva o sintoma e a causa-raiz.

## 🧱 Padrões de código

- **Tools novas**: decoradas com `@tool` em `arquimedes/tools/<nome>.py`
  e exportadas em `arquimedes/tools/__init__.py` (entram automaticamente
  em `all_tools`, que alimenta tanto LangGraph quanto MCP).
- **Memory backends novos**: implementem `put`, `search`, `get`,
  `delete` retornando `StoreRecord` de `shared/store_types.py`. O
  factory `shared/memory.py:get_store()` faz a seleção via env.
- **LLM providers novos**: estendem `_PROVIDER_PREFIXES` em
  `shared/llm.py` e implementam o branch dentro de `get_llm()`.
- **Documentação**: PT-BR é o padrão. Use emojis em headings (👍) mas
  com moderação no corpo.

## 🔐 Segurança

- **Nunca** commite `.env`. Confira com `git status` antes de cada
  commit. O `.gitignore` já protege, mas double-check.
- Chaves de API rotacionam a cada entrevista — evite hardcoded.
- Para o MCP server SSE em produção, ponha um reverse-proxy com auth
  (a porta 8765 não tem autenticação nativa).

## 🐛 Reportando bugs

Abra uma issue com:

1. O que você tentou (`curl`, comando ou screenshot).
2. O que esperava.
3. O que aconteceu (logs do `/tmp/api.log` ou console do browser).
4. Versão / commit hash (`git rev-parse --short HEAD`).
