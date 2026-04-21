"""Arquimedes — Math-for-ML adaptive tutor.

LangGraph topology:

    START
      ↓  (heuristic entry router)
    rag_retrieve ──┐
                   ↓
                assistant ←──────────── tools
                   │                      ↑
            tools_condition ──────────────┘
                   │
                   ↓  (no tool calls)
               write_memory
                   │
               should_continue
                ↙          ↘
     summarize_conversation   END
                   ↓
                  END

- LCEL ``build_assistant_chain`` invoked by the assistant node.
- Structured student-fact extraction in write_memory (Pydantic schema).
- Semantic-memory retrieval in assistant (queries Store with the last
  user message).
- rag_retrieve proactively injects textbook passages when the learner's
  query looks citation-seeking (heuristic router).
"""

from typing import Literal

from langchain_core.messages import (
    HumanMessage,
    RemoveMessage,
    SystemMessage,
)
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.store.base import BaseStore

from arquimedes.chains import build_assistant_chain, build_memory_extractor_chain
from arquimedes.rag.retrieval import format_passages, search as rag_search
from arquimedes.routing import entry_route, last_human_content
from arquimedes.tools import all_tools
from shared.configuration import Configuration
from shared.llm import get_llm
from shared.memory import get_checkpointer, get_store


# ── State ──────────────────────────────────────────────────────────────
class State(MessagesState):
    summary: str
    retrieved_context: str


# ── Nodes ──────────────────────────────────────────────────────────────
def rag_retrieve(state: State) -> dict:
    """Proactively pull textbook passages before the assistant runs."""
    query = last_human_content(state["messages"])
    if not query:
        return {}
    try:
        docs = rag_search(query, k=4)
    except Exception:
        return {}
    if not docs:
        return {}
    return {"retrieved_context": format_passages(docs)}


def assistant(state: State, config: RunnableConfig, store: BaseStore):
    """Invoke LLM with tools via an LCEL chain; inject profile + retrieved context."""
    conf = Configuration.from_runnable_config(config)

    # Retrieve student profile from Store. When the store supports semantic
    # search (SemanticStore), query it with the latest user message so only
    # relevant facts are injected. Fall back to prefix scan for InMemoryStore.
    namespace = ("student_profile", conf.user_id)
    query = last_human_content(state["messages"])
    try:
        existing = store.search(namespace, query=query or None, limit=5)
    except TypeError:
        existing = store.search(namespace)
    profile_ctx = "\n".join(m.value.get("content", "") for m in existing)

    summary = state.get("summary", "")
    retrieved = state.get("retrieved_context", "")

    extra_parts: list[str] = []
    if profile_ctx:
        extra_parts.append(f"Student profile from previous sessions:\n{profile_ctx}")
    if summary:
        extra_parts.append(f"Conversation summary so far:\n{summary}")
    if retrieved:
        extra_parts.append(
            "Retrieved passages from the math knowledge base — quote them "
            "when relevant and cite the source:\n" + retrieved
        )
    extra_context = "\n\n".join(extra_parts)

    chain = build_assistant_chain(model=conf.model_name, extra_context=extra_context)
    response = chain.invoke({"messages": state["messages"]})
    return {"messages": [response]}


def write_memory(state: State, config: RunnableConfig, store: BaseStore):
    """Extract structured student facts via Pydantic-schema chain, persist to Store."""
    conf = Configuration.from_runnable_config(config)
    namespace = ("student_profile", conf.user_id)

    # Keep only human turns + final AI turns (drop ToolMessage + tool_calls pairs)
    # so the extractor prompt doesn't send orphan tool messages to providers
    # that validate tool_calls/tool_result pairing.
    clean = [
        m for m in state["messages"][-12:]
        if getattr(m, "type", None) in ("human", "ai")
        and not getattr(m, "tool_calls", None)
    ]
    recent = clean[-6:]
    if not recent:
        return {}

    try:
        chain = build_memory_extractor_chain(model=conf.model_name)
        update = chain.invoke({"messages": recent})
    except Exception:
        llm = get_llm(model=conf.model_name)
        extract_prompt = (
            "Summarize what we learned about the student in one paragraph. "
            "If nothing new, reply 'No new information'."
        )
        result = llm.invoke([SystemMessage(content=extract_prompt)] + list(recent))
        if "no new information" not in result.content.lower():
            store.put(namespace, "profile", {"content": result.content})
        return {}

    if not update.has_new_information or not update.facts:
        return {}

    for fact in update.facts:
        fact_id = f"{fact.topic}:{fact.level}"
        store.put(
            namespace,
            fact_id,
            {
                "content": (
                    f"[{fact.topic} — {fact.level} (conf {fact.confidence:.2f})] "
                    f"{fact.evidence}"
                ),
                "topic": fact.topic,
                "level": fact.level,
                "confidence": fact.confidence,
            },
        )
    return {}


def should_continue(state: State) -> Literal["summarize_conversation", "__end__"]:
    if len(state["messages"]) > 10:
        return "summarize_conversation"
    return END


def summarize_conversation(state: State, config: RunnableConfig):
    conf = Configuration.from_runnable_config(config)
    summary = state.get("summary", "")
    if summary:
        prompt = (
            f"Previous summary: {summary}\n\n"
            "Extend the summary with the new messages. Highlight student progress:"
        )
    else:
        prompt = (
            "Summarize the lesson so far, highlighting what was taught and the "
            "student's progress:"
        )

    llm = get_llm(model=conf.model_name)
    messages = state["messages"] + [HumanMessage(content=prompt)]
    response = llm.invoke(messages)

    delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][:-2]]
    return {"summary": response.content, "messages": delete_messages}


# ── Graph ──────────────────────────────────────────────────────────────
builder = StateGraph(State, config_schema=Configuration)

builder.add_node("rag_retrieve", rag_retrieve)
builder.add_node("assistant", assistant)
builder.add_node("tools", ToolNode(all_tools))
builder.add_node("write_memory", write_memory)
builder.add_node("summarize_conversation", summarize_conversation)

# Entry router: cheap keyword heuristic → rag_retrieve vs. assistant.
builder.add_conditional_edges(
    START,
    entry_route,
    {"rag_retrieve": "rag_retrieve", "assistant": "assistant"},
)
builder.add_edge("rag_retrieve", "assistant")
builder.add_conditional_edges(
    "assistant",
    tools_condition,
    {"tools": "tools", "__end__": "write_memory"},
)
builder.add_edge("tools", "assistant")
builder.add_conditional_edges("write_memory", should_continue)
builder.add_edge("summarize_conversation", END)

graph = builder.compile(
    checkpointer=get_checkpointer(),
    store=get_store(),
)
