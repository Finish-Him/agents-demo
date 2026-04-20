"""Archimedes — Math-for-ML adaptive tutor.

LangGraph ReAct agent with:
- LCEL assistant chain (prompt | llm.bind_tools)
- Structured memory extraction via Pydantic
- ToolNode loop with tools_condition
- Profile-aware system prompt (long-term Store) + summarization
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
from arquimedes.tools import all_tools
from shared.configuration import Configuration
from shared.llm import get_llm
from shared.memory import get_checkpointer, get_store


# ── State ──────────────────────────────────────────────────────────────
class State(MessagesState):
    summary: str


# ── Nodes ──────────────────────────────────────────────────────────────
def assistant(state: State, config: RunnableConfig, store: BaseStore):
    """Invoke LLM with tools via an LCEL chain; inject student profile from Store."""
    conf = Configuration.from_runnable_config(config)

    # Retrieve student profile from Store (prefix scan; Phase 3 will switch to semantic).
    user_id = conf.user_id
    namespace = ("student_profile", user_id)
    existing = store.search(namespace)
    profile_ctx = "\n".join(m.value.get("content", "") for m in existing)

    summary = state.get("summary", "")
    extra_parts: list[str] = []
    if profile_ctx:
        extra_parts.append(f"Student profile from previous sessions:\n{profile_ctx}")
    if summary:
        extra_parts.append(f"Conversation summary so far:\n{summary}")
    extra_context = "\n\n".join(extra_parts)

    chain = build_assistant_chain(model=conf.model_name, extra_context=extra_context)
    response = chain.invoke({"messages": state["messages"]})
    return {"messages": [response]}


def write_memory(state: State, config: RunnableConfig, store: BaseStore):
    """Extract structured student facts via Pydantic-schema chain, persist to Store."""
    conf = Configuration.from_runnable_config(config)
    namespace = ("student_profile", conf.user_id)

    # Only look at the last 6 messages to keep extraction cheap.
    recent = state["messages"][-6:]
    if not recent:
        return {}

    try:
        chain = build_memory_extractor_chain(model=conf.model_name)
        update = chain.invoke({"messages": recent})
    except Exception:
        # Some models don't support structured output reliably. Fall back
        # to a plain extractor that stores the raw summary string.
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

    # Persist each fact as its own record (prepares Phase 3 semantic store).
    for i, fact in enumerate(update.facts):
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

builder.add_node("assistant", assistant)
builder.add_node("tools", ToolNode(all_tools))
builder.add_node("write_memory", write_memory)
builder.add_node("summarize_conversation", summarize_conversation)

builder.add_edge(START, "assistant")
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
