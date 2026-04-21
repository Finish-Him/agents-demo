"""FastAPI server exposing all 3 agents via REST + SSE streaming."""

import json
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

load_dotenv()

from shared.llm import DEFAULT_MODEL

# Import agents (triggers graph compilation)
from prometheus.agent import graph as prometheus_graph
from arquimedes.agent import graph as arquimedes_graph
from atlas.agent import graph as atlas_graph

AGENTS = {
    "prometheus": {
        "graph": prometheus_graph,
        "name": "Prometheus",
        "description": "Especialista em governança de IA e privacidade — GDPR, CCPA, EU AI Act, NIST AI RMF.",
        "lang": "pt-BR",
        "examples": [
            "Quais são as multas da GDPR para vazamento de dados?",
            "Avalie o risco da EU AI Act para uma IA de triagem de currículos.",
            "Gere um checklist de conformidade GDPR para um sistema de IA.",
        ],
    },
    "arquimedes": {
        "graph": arquimedes_graph,
        "name": "Arquimedes",
        "description": "Tutor adaptativo de matemática para ML — álgebra linear, cálculo, probabilidade e estatística. RAG sobre Strang/Deisenroth/OpenStax; derivações passo a passo.",
        "lang": "pt-BR",
        "examples": [
            "Explique autovetores com uma analogia geométrica e cite o livro-texto.",
            "Derive passo a passo o gradiente da função de perda MSE.",
            "Exercício intermediário de Teorema de Bayes — depois corrija minha resposta.",
            "Qual a diferença entre MLE e MAP na estimação?",
        ],
    },
    "atlas": {
        "graph": atlas_graph,
        "name": "Atlas",
        "description": "Consultor de stack técnico — explora seus repositórios no GitHub, Spaces do HuggingFace e recomenda tecnologias.",
        "lang": "pt-BR",
        "examples": [
            "Liste meus repositórios do GitHub.",
            "O que tem no meu projeto youtube_summarizer?",
            "Recomende uma stack para expor um modelo de ML como API.",
        ],
    },
}

# Models available in the UI selector
AVAILABLE_MODELS = [
    {"id": "qwen/qwen3-235b-a22b", "name": "Qwen3 235B (OpenRouter)", "speed": "fast"},
    {"id": "deepseek/deepseek-chat-v3-0324", "name": "DeepSeek V3 (OpenRouter)", "speed": "medium"},
    {"id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash (Google)", "speed": "fast"},
    {"id": "gpt-4o-mini", "name": "GPT-4o Mini (OpenAI)", "speed": "fast"},
    {"id": "claude-sonnet-4-20250514", "name": "Claude Sonnet 4 (Anthropic)", "speed": "medium"},
    {"id": "hf/Qwen/Qwen2.5-7B-Instruct", "name": "Qwen2.5 7B (HF Inference)", "speed": "medium"},
]


class ChatRequest(BaseModel):
    message: str
    thread_id: str | None = None
    user_id: str = "default-user"
    model_name: str | None = None


class ChatResponse(BaseModel):
    response: str
    thread_id: str
    agent: str


app = FastAPI(
    title="Agents Demo — Factored Interview",
    description="3 LangGraph agents: Prometheus, Arquimedes, Atlas — with SSE streaming",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "agents": list(AGENTS.keys())}


@app.get("/agents")
async def list_agents():
    return {
        name: {
            "name": info["name"],
            "description": info["description"],
            "lang": info["lang"],
            "examples": info["examples"],
        }
        for name, info in AGENTS.items()
    }


@app.get("/models")
async def list_models():
    return {"default": DEFAULT_MODEL, "available": AVAILABLE_MODELS}


# ── Blocking endpoint (backwards-compatible) ──────────────────────────
@app.post("/chat/{agent_name}", response_model=ChatResponse)
async def chat(agent_name: str, req: ChatRequest):
    if agent_name not in AGENTS:
        raise HTTPException(
            status_code=404,
            detail=f"Agent '{agent_name}' not found. Available: {list(AGENTS.keys())}",
        )

    agent_info = AGENTS[agent_name]
    graph = agent_info["graph"]
    thread_id = req.thread_id or str(uuid.uuid4())

    config = {
        "configurable": {
            "thread_id": thread_id,
            "user_id": req.user_id,
            "model_name": req.model_name or DEFAULT_MODEL,
        }
    }

    result = await graph.ainvoke(
        {"messages": [("user", req.message)]},
        config=config,
    )

    ai_message = result["messages"][-1]
    return ChatResponse(
        response=ai_message.content,
        thread_id=thread_id,
        agent=agent_name,
    )


# ── SSE streaming endpoint ────────────────────────────────────────────
@app.post("/chat/{agent_name}/stream")
async def chat_stream(agent_name: str, req: ChatRequest):
    if agent_name not in AGENTS:
        raise HTTPException(
            status_code=404,
            detail=f"Agent '{agent_name}' not found. Available: {list(AGENTS.keys())}",
        )

    agent_info = AGENTS[agent_name]
    graph = agent_info["graph"]
    thread_id = req.thread_id or str(uuid.uuid4())

    config = {
        "configurable": {
            "thread_id": thread_id,
            "user_id": req.user_id,
            "model_name": req.model_name or DEFAULT_MODEL,
        }
    }

    async def event_generator():
        # Send thread_id as first event
        yield {"event": "metadata", "data": json.dumps({"thread_id": thread_id, "agent": agent_name})}

        async for event in graph.astream_events(
            {"messages": [("user", req.message)]},
            config=config,
            version="v2",
        ):
            kind = event["event"]
            # Only stream tokens that the assistant node produces — otherwise
            # internal LLM calls (memory extraction, summarization) would
            # leak strings like "No new information" into the chat response.
            node = event.get("metadata", {}).get("langgraph_node")
            if kind == "on_chat_model_stream" and node == "assistant":
                token = event["data"]["chunk"].content
                if token:
                    yield {"event": "token", "data": token}
            elif kind == "on_tool_start":
                tool_name = event.get("name", "unknown")
                yield {"event": "tool_start", "data": tool_name}
            elif kind == "on_tool_end":
                tool_name = event.get("name", "unknown")
                yield {"event": "tool_end", "data": tool_name}

        yield {"event": "done", "data": ""}

    return EventSourceResponse(event_generator())


# ── Serve React frontend (static files + SPA fallback) ────────────────
FRONTEND_DIR = Path(__file__).parent / "frontend" / "dist"

# Paths that should NOT be caught by the SPA fallback
_API_PREFIXES = {"health", "agents", "models", "chat", "docs", "redoc", "openapi.json"}

if FRONTEND_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def spa_fallback(request: Request, full_path: str):
        # Never intercept FastAPI's own routes
        first_segment = full_path.split("/")[0] if full_path else ""
        if first_segment in _API_PREFIXES:
            raise HTTPException(status_code=404, detail="Not found")
        # Serve static file if it exists, otherwise index.html (SPA)
        file = FRONTEND_DIR / full_path
        if file.is_file():
            return FileResponse(file)
        return FileResponse(FRONTEND_DIR / "index.html")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
