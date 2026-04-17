"""Archimedes — Adaptive AI Tutor Agent.

LangGraph ReAct agent with tool calling, student profile memory (Store),
conversation persistence (Checkpointer), and summarization.
Demonstrates: ReAct loop, profile memory, adaptive routing, tools_condition.
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

from arquimedes.prompts import SYSTEM_PROMPT
from arquimedes.tools import all_tools
from shared.configuration import Configuration
from shared.llm import get_llm
from shared.memory import get_checkpointer, get_store


# ── State ──────────────────────────────────────────────────────────────
class State(MessagesState):
    summary: str


# ── Nodes ──────────────────────────────────────────────────────────────
def assistant(state: State, config: RunnableConfig, store: BaseStore):
    """Invoke LLM with tools, injecting student profile from Store."""
    conf = Configuration.from_runnable_config(config)
    llm = get_llm(model=conf.model_name)
    llm_with_tools = llm.bind_tools(all_tools)

    # Retrieve student profile from Store
    user_id = conf.user_id
    namespace = ("student_profile", user_id)
    existing = store.search(namespace)
    profile_ctx = "\n".join(m.value.get("content", "") for m in existing)

    # Build system message
    summary = state.get("summary", "")
    parts = [SYSTEM_PROMPT]
    if profile_ctx:
        parts.append(f"\nStudent profile from previous sessions:\n{profile_ctx}")
    if summary:
        parts.append(f"\nConversation summary so far:\n{summary}")

    sys_msg = SystemMessage(content="\n".join(parts))
    response = llm_with_tools.invoke([sys_msg] + state["messages"])
    return {"messages": [response]}


def write_memory(state: State, config: RunnableConfig, store: BaseStore):
    """Extract and persist student profile (level, strengths, weaknesses)."""
    conf = Configuration.from_runnable_config(config)
    user_id = conf.user_id
    namespace = ("student_profile", user_id)

    llm = get_llm(model=conf.model_name)
    extract_prompt = (
        "Analyze the conversation and extract information about the student: "
        "level in each subject, strengths, weaknesses, topics studied, "
        "observed progress. Return a brief paragraph. "
        "If there is no new information, reply 'No new information'."
    )
    result = llm.invoke(
        [SystemMessage(content=extract_prompt)] + state["messages"][-6:]
    )
    if "no new information" not in result.content.lower():
        store.put(namespace, "profile", {"content": result.content})
    return {}


def should_continue(state: State) -> Literal["summarize_conversation", "__end__"]:
    """Summarize when conversation exceeds 10 messages."""
    if len(state["messages"]) > 10:
        return "summarize_conversation"
    return END


def summarize_conversation(state: State):
    """Compress conversation history, keeping only the last 2 messages."""
    summary = state.get("summary", "")
    if summary:
        prompt = (
            f"Previous summary: {summary}\n\n"
            "Extend the summary with the new messages. Highlight student progress:"
        )
    else:
        prompt = "Create a summary of the lesson so far, highlighting what was taught and the student's progress:"

    llm = get_llm()
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
