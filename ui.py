"""Gradio Web UI — 3 tabs for Prometheus, Arquimedes, and Atlas agents."""

import uuid

import gradio as gr
from dotenv import load_dotenv

load_dotenv()

from prometheus.agent import graph as prometheus_graph
from arquimedes.agent import graph as arquimedes_graph
from atlas.agent import graph as atlas_graph

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
        "title": "📚 Archimedes — AI Tutor",
        "description": (
            "Adaptive tutor that teaches ML, deep learning, Python, and LLM agents "
            "at your level. Assesses knowledge, generates exercises, explains with "
            "analogies, and tracks your progress."
        ),
        "examples": [
            "I want to learn machine learning from scratch.",
            "Explain the transformer attention mechanism with a simple analogy.",
            "Generate an intermediate exercise on gradient descent.",
            "What resources do you recommend for learning about LLM agents?",
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


def create_chat_fn(agent_key: str):
    """Create a chat function for a specific agent."""
    graph = AGENTS[agent_key]["graph"]

    def chat_fn(message: str, history: list, thread_id: str):
        if not thread_id:
            thread_id = str(uuid.uuid4())

        config = {
            "configurable": {
                "thread_id": thread_id,
                "user_id": "demo-user",
            }
        }

        result = graph.invoke(
            {"messages": [("user", message)]},
            config=config,
        )

        ai_message = result["messages"][-1]
        return ai_message.content

    return chat_fn


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

                chat_fn = create_chat_fn(agent_key)

                def respond(message, history, thread_id, _chat_fn=chat_fn):
                    response = _chat_fn(message, history, thread_id)
                    history.append({"role": "user", "content": message})
                    history.append({"role": "assistant", "content": response})
                    return "", history

                msg.submit(
                    respond,
                    inputs=[msg, chatbot, thread_state],
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
