"""Gradio Web UI — 3 tabs for Prometheus, Arquimedes, and Atlas agents.

Features: token-by-token streaming, model selector, conversation memory.
"""

import uuid

import gradio as gr
from dotenv import load_dotenv

load_dotenv()

from prometheus.agent import graph as prometheus_graph
from arquimedes.agent import graph as arquimedes_graph
from atlas.agent import graph as atlas_graph
from shared.llm import DEFAULT_MODEL

AGENTS = {
    "prometheus": {
        "graph": prometheus_graph,
        "title": "🔥 Prometheus — AI Compliance",
        "description": (
            "AI governance and data-privacy compliance specialist. "
            "Looks up GDPR, CCPA, EU AI Act, and NIST AI RMF regulations, "
            "assesses AI risk levels, calculates penalties, and generates compliance checklists."
        ),
        "examples": [
            "What are the GDPR penalties for a data breach?",
            "Assess the EU AI Act risk level for a hiring screening AI system.",
            "Generate a GDPR compliance checklist for an AI system.",
            "What is the deadline for a GDPR breach notification?",
        ],
    },
    "arquimedes": {
        "graph": arquimedes_graph,
        "title": "📚 Arquimedes — Tutor de Matemática para ML",
        "description": (
            "Tutor adaptativo de álgebra linear, cálculo, probabilidade e "
            "estatística — com RAG sobre Strang/Deisenroth/OpenStax, "
            "derivações passo a passo via SymPy e solver fine-tuned com LoRA."
        ),
        "examples": [
            "Explique autovetores com uma analogia geométrica e cite o livro-texto.",
            "Derive passo a passo o gradiente da função de perda MSE.",
            "Exercício intermediário de Teorema de Bayes — depois corrija minha resposta.",
            "Qual a diferença entre MLE e MAP na estimação?",
        ],
    },
    "atlas": {
        "graph": atlas_graph,
        "title": "🗺️ Atlas — Stack Specialist",
        "description": (
            "Tech consultant that explores your GitHub repos, HuggingFace Spaces, "
            "analyzes project structures, and recommends technologies based on "
            "your existing stack."
        ),
        "examples": [
            "List all my GitHub repositories.",
            "Analyze the youtube_summarizer project structure.",
            "Search my HuggingFace spaces.",
            "What technology should I use to deploy an ML model as an API?",
        ],
    },
}

MODEL_CHOICES = [
    ("DeepSeek V3 (OpenRouter)", "deepseek/deepseek-chat-v3-0324"),
    ("Gemini 2.0 Flash (Google) ⚡", "gemini-2.0-flash"),
    ("GPT-4o Mini (OpenAI) ⚡", "gpt-4o-mini"),
    ("Claude Sonnet 4 (Anthropic)", "claude-sonnet-4-20250514"),
]


def create_stream_fn(agent_key: str):
    """Create an async streaming chat function for a specific agent."""
    graph = AGENTS[agent_key]["graph"]

    async def stream_fn(message: str, history: list, thread_id: str, model_name: str):
        if not thread_id:
            thread_id = str(uuid.uuid4())

        config = {
            "configurable": {
                "thread_id": thread_id,
                "user_id": "demo-user",
                "model_name": model_name or DEFAULT_MODEL,
            }
        }

        # Stream tokens as they arrive
        partial = ""
        async for event in graph.astream_events(
            {"messages": [("user", message)]},
            config=config,
            version="v2",
        ):
            if event["event"] == "on_chat_model_stream":
                token = event["data"]["chunk"].content
                if token:
                    partial += token
                    yield partial

    return stream_fn


def build_ui() -> gr.Blocks:
    """Build the Gradio Blocks UI with 3 agent tabs."""

    with gr.Blocks(
        title="Agents Demo — Factored Interview",
        theme=gr.themes.Soft(
            primary_hue="indigo",
            secondary_hue="purple",
        ),
    ) as demo:
        gr.Markdown(
            "# 🤖 Agents Demo — Factored.ai Interview\n"
            "Three functional LangGraph agents showcasing ReAct tools, memory, "
            "and external API integration.\n\n"
            "**Built by Moisés Costa** | LangGraph + LangChain + LangSmith + OpenRouter"
        )

        # Global model selector
        model_dropdown = gr.Dropdown(
            choices=MODEL_CHOICES,
            value=DEFAULT_MODEL,
            label="🧠 Model",
            info="⚡ = fast (1-3s) | others = smart (5-15s)",
            interactive=True,
        )

        for agent_key, agent_info in AGENTS.items():
            with gr.Tab(agent_info["title"]):
                gr.Markdown(f"### {agent_info['title']}\n{agent_info['description']}")

                thread_state = gr.State(str(uuid.uuid4()))

                chatbot = gr.Chatbot(
                    height=450,
                    type="messages",
                    show_copy_button=True,
                )
                msg = gr.Textbox(
                    placeholder="Type your message...",
                    label="Message",
                    lines=1,
                )

                stream_fn = create_stream_fn(agent_key)

                async def respond(message, history, thread_id, model_name, _stream_fn=stream_fn):
                    history.append({"role": "user", "content": message})
                    history.append({"role": "assistant", "content": ""})
                    async for partial in _stream_fn(message, history, thread_id, model_name):
                        history[-1]["content"] = partial
                        yield "", history

                msg.submit(
                    respond,
                    inputs=[msg, chatbot, thread_state, model_dropdown],
                    outputs=[msg, chatbot],
                )

                gr.Markdown("**Examples:**")
                for ex in agent_info["examples"]:
                    gr.Button(ex, size="sm").click(
                        lambda ex=ex: ex,
                        outputs=[msg],
                    )

        gr.Markdown(
            "---\n"
            "**Tech Stack:** LangGraph · LangChain · LangSmith · OpenRouter / OpenAI / Anthropic / Gemini · "
            "FastAPI · Gradio · Docker\n\n"
            "**Source:** [GitHub](https://github.com/Finish-Him/agents-demo) · "
            "[LangSmith Dashboard](https://smith.langchain.com)\n\n"
            "**Built by Moisés Costa** for Factored.ai Senior GenAI Engineer interview"
        )

    return demo


if __name__ == "__main__":
    demo = build_ui()
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
