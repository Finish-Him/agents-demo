"""FastAPI server exposing all 3 agents via REST + SSE streaming."""

import uuid
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

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


class ChatRequest(BaseModel):
    message: str
    thread_id: str | None = None
    user_id: str = "default-user"


class ChatResponse(BaseModel):
    response: str
    thread_id: str
    agent: str


app = FastAPI(
    title="Agents Demo — Factored Interview",
    description="3 LangGraph agents: Prometheus (DETRAN), Arquimedes (Teaching), Atlas (Stack)",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "agents": list(AGENTS.keys())}


@app.get("/agents")
def list_agents():
    return {
        name: {
            "name": info["name"],
            "description": info["description"],
            "lang": info["lang"],
            "examples": info["examples"],
        }
        for name, info in AGENTS.items()
    }


@app.post("/chat/{agent_name}", response_model=ChatResponse)
def chat(agent_name: str, req: ChatRequest):
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
        }
    }

    result = graph.invoke(
        {"messages": [("user", req.message)]},
        config=config,
    )

    ai_message = result["messages"][-1]
    return ChatResponse(
        response=ai_message.content,
        thread_id=thread_id,
        agent=agent_name,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
