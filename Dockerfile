FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose ports: 8000 (FastAPI) and 7860 (Gradio)
EXPOSE 8000 7860

# Default: run Gradio UI (includes both API + UI)
CMD ["python", "ui.py"]
