"""FastAPI server exposing all 3 agents via REST + SSE streaming."""

import json
import uuid

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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
        "description": "AI governance and data-privacy compliance specialist — GDPR, CCPA, EU AI Act, NIST AI RMF.",
        "lang": "en",
        "examples": [
            "What are the GDPR penalties for a data breach?",
            "Assess the EU AI Act risk level for a hiring screening AI.",
            "Generate a GDPR compliance checklist for an AI system.",
        ],
    },
    "arquimedes": {
        "graph": arquimedes_graph,
        "name": "Archimedes",
        "description": "Adaptive AI tutor — teaches ML, Python, deep learning, and LLM agents at your level.",
        "lang": "en",
        "examples": [
            "I want to learn machine learning from scratch.",
            "Explain transformers with a simple analogy.",
            "Generate an intermediate exercise on gradient descent.",
        ],
    },
    "atlas": {
        "graph": atlas_graph,
        "name": "Atlas",
        "description": "Tech stack consultant — explores your GitHub repos, HF Spaces, and recommends technologies.",
        "lang": "en",
        "examples": [
            "List all my GitHub repositories.",
            "What's in my youtube_summarizer project?",
            "Recommend a technology for deploying an ML model as an API.",
        ],
    },
}

# Models available in the UI selector
AVAILABLE_MODELS = [
    {"id": "deepseek/deepseek-chat-v3-0324", "name": "DeepSeek V3 (OpenRouter)", "speed": "medium"},
    {"id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash (Google)", "speed": "fast"},
    {"id": "gpt-4o-mini", "name": "GPT-4o Mini (OpenAI)", "speed": "fast"},
    {"id": "claude-sonnet-4-20250514", "name": "Claude Sonnet 4 (Anthropic)", "speed": "medium"},
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
            if event["event"] == "on_chat_model_stream":
                token = event["data"]["chunk"].content
                if token:
                    yield {"event": "token", "data": token}

        yield {"event": "done", "data": ""}

    return EventSourceResponse(event_generator())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
