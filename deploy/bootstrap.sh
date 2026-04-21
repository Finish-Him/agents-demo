#!/usr/bin/env bash
#
# One-shot bootstrap for the Archimedes demo on a fresh VPS (Ubuntu 22.04+).
#
# Usage on the VPS:
#
#     bash <(curl -sL https://raw.githubusercontent.com/Finish-Him/agents-demo/claude/arquimedes-math-agent-Mj90C/deploy/bootstrap.sh)
#
# or, after cloning:
#
#     cd agents-demo && bash deploy/bootstrap.sh
#
# What it does:
#   1. Install docker + docker-compose plugin if missing.
#   2. Clone / pull the claude branch.
#   3. Ensure .env exists (copies from .env.example if absent).
#   4. `docker compose up -d --build` (main app + MCP profile).
#   5. Ingest the math corpus inside the container.
#   6. Point nginx :80 at :8000 with a reverse-proxy snippet.
#   7. Health-check and print the public URL.

set -euo pipefail

REPO="${REPO:-https://github.com/Finish-Him/agents-demo.git}"
BRANCH="${BRANCH:-claude/arquimedes-math-agent-Mj90C}"
APP_DIR="${APP_DIR:-/opt/agents-demo}"
PUBLIC_HOST="${PUBLIC_HOST:-}"      # optional, e.g. arquimedes.example.com

# ── 1. Dependencies ──────────────────────────────────────────────────
install_docker() {
    echo "[bootstrap] installing docker..."
    apt-get update -y
    apt-get install -y ca-certificates curl gnupg git
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
        | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
      https://download.docker.com/linux/ubuntu $(. /etc/os-release; echo "$VERSION_CODENAME") stable" \
      > /etc/apt/sources.list.d/docker.list
    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    systemctl enable --now docker
}

command -v docker >/dev/null || install_docker
command -v docker compose >/dev/null 2>&1 || install_docker

# ── 2. Checkout ──────────────────────────────────────────────────────
if [ -d "$APP_DIR/.git" ]; then
    echo "[bootstrap] pulling $BRANCH into $APP_DIR"
    git -C "$APP_DIR" fetch origin
    git -C "$APP_DIR" checkout "$BRANCH"
    git -C "$APP_DIR" pull --ff-only origin "$BRANCH"
else
    echo "[bootstrap] cloning $REPO -> $APP_DIR"
    git clone "$REPO" "$APP_DIR"
    git -C "$APP_DIR" checkout "$BRANCH"
fi
cd "$APP_DIR"

# ── 3. .env ──────────────────────────────────────────────────────────
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "[bootstrap] ⚠  created .env from .env.example — fill in secrets, then rerun this script."
        echo "              Required: OPENROUTER_API_KEY, OPENAI_API_KEY, HF_TOKEN, LANGSMITH_API_KEY"
        exit 2
    fi
fi

# ── 4. Docker compose ────────────────────────────────────────────────
echo "[bootstrap] docker compose up -d --build ..."
docker compose pull || true
docker compose build
docker compose up -d

# MCP server (SSE) — optional profile
docker compose --profile mcp up -d --build || echo "[bootstrap] MCP profile skipped"

# ── 5. Ingest the math RAG corpus (idempotent) ──────────────────────
echo "[bootstrap] ingesting RAG corpus..."
docker compose exec -T agents-api python -m arquimedes.rag.ingest --reset || {
    echo "[bootstrap] corpus ingest failed (non-fatal — can be run later)"
}

# ── 6. Nginx reverse proxy on :80 ────────────────────────────────────
if command -v nginx >/dev/null 2>&1; then
    NGINX_CONF=/etc/nginx/sites-available/arquimedes.conf
    cat > "$NGINX_CONF" <<NGINX
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _ ${PUBLIC_HOST};

    # Proxy the FastAPI app
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # Keep SSE streams alive
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }

    # MCP SSE endpoint (optional)
    location /mcp/ {
        proxy_pass http://127.0.0.1:8765/;
        proxy_http_version 1.1;
        proxy_buffering off;
        proxy_read_timeout 3600s;
    }
}
NGINX
    ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/arquimedes.conf
    rm -f /etc/nginx/sites-enabled/default
    nginx -t && systemctl reload nginx
fi

# ── 7. Health check ──────────────────────────────────────────────────
sleep 5
echo "[bootstrap] health check:"
curl -sf http://127.0.0.1:8000/health && echo
if [ -n "$PUBLIC_HOST" ]; then
    PUBLIC_URL="http://$PUBLIC_HOST"
else
    IP=$(curl -s -m 3 https://api.ipify.org || hostname -I | awk '{print $1}')
    PUBLIC_URL="http://$IP"
fi
echo
echo "[bootstrap] ✅ Archimedes is live at: $PUBLIC_URL"
echo "[bootstrap]    API docs:             $PUBLIC_URL/docs"
echo "[bootstrap]    MCP SSE (if enabled): $PUBLIC_URL/mcp/sse"
