# ── Stage 1: Build React frontend ──────────────────────────────────
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# ── Stage 2: Python API ───────────────────────────────────────────
FROM python:3.11-slim
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy built frontend into the image
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Expose ports: 8000 (FastAPI) and 7860 (Gradio)
EXPOSE 8000 7860

# Default: run Gradio UI (includes both API + UI)
CMD ["python", "ui.py"]
