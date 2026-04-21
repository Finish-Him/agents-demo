# Deploying Archimedes to a VPS

One-shot script: `deploy/bootstrap.sh`.

Tested on Ubuntu 22.04 / 24.04, Hostinger & DigitalOcean droplets.

## Quick start (you run these commands)

```bash
# 1. SSH into the VPS
ssh root@187.77.37.158
# password: Arquimedes@2026   (rotate after the interview)

# 2. Pull the bootstrap script and run it
curl -sLO https://raw.githubusercontent.com/Finish-Him/agents-demo/claude/arquimedes-math-agent-Mj90C/deploy/bootstrap.sh
bash bootstrap.sh
```

First run creates `/opt/agents-demo/.env` from `.env.example` and exits
with a reminder to fill in the secrets. Edit it:

```bash
nano /opt/agents-demo/.env
# fill in:
#   OPENROUTER_API_KEY
#   OPENAI_API_KEY
#   HF_TOKEN
#   LANGSMITH_API_KEY
#   GOOGLE_API_KEY (optional)
#   ANTHROPIC_API_KEY (optional)
#   POSTGRES_URL (optional — Supabase)
```

Then re-run:

```bash
cd /opt/agents-demo && bash deploy/bootstrap.sh
```

## What the script does

1. Installs Docker + Compose plugin if missing.
2. Clones the repo into `/opt/agents-demo` and checks out
   `claude/arquimedes-math-agent-Mj90C`.
3. Builds the images and starts `agents-api` + `agents-demo` (Gradio
   fallback). `--profile mcp` also starts the MCP SSE endpoint on :8765.
4. Runs `python -m arquimedes.rag.ingest --reset` inside the container
   so the Chroma corpus is populated.
5. Writes an nginx reverse-proxy on port 80 → `127.0.0.1:8000`, keeping
   `proxy_buffering off` so SSE streams flow.
6. Health-checks and prints the public URL.

## Updating to a new commit

```bash
ssh root@187.77.37.158
cd /opt/agents-demo
git pull --ff-only origin claude/arquimedes-math-agent-Mj90C
bash deploy/bootstrap.sh
```

The script is idempotent — re-running it just pulls + rebuilds.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `docker: command not found` after install | `systemctl status docker`; re-run the script. |
| Streaming responses arrive as one chunk | `proxy_buffering off;` missing in nginx. Re-run the bootstrap — it rewrites the config. |
| `/health` returns nginx 404 | nginx is still serving the default site. `rm -f /etc/nginx/sites-enabled/default && systemctl reload nginx`. |
| RAG tool returns "unavailable" | `docker compose exec -T agents-api python -m arquimedes.rag.ingest --reset` |
| LangSmith shows no traces | Check `LANGSMITH_API_KEY` and `LANGSMITH_TRACING=true` in `/opt/agents-demo/.env`; `docker compose restart agents-api`. |
| Port 22 closed for inbound ops | Hostinger firewall. Console from Hostinger panel still works. |

## Post-deploy

After the script prints `✅ Archimedes is live`:

- Visit `http://187.77.37.158/` — React UI + chat.
- Visit `http://187.77.37.158/docs` — FastAPI OpenAPI.
- Click the "How it works" button in the bottom-right of the chat to
  self-guide through the 9 concepts.
- Rotate the SSH password and all API keys before real-world exposure.
