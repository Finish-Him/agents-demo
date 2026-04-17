"""Prometheus — AI Governance & Data Privacy Compliance Agent.

LangGraph ReAct agent with tool calling, conversation summarization,
and long-term user memory. Demonstrates: tools_condition, ToolNode,
conditional routing, RemoveMessage, Store, Checkpointer.
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

from prometheus.prompts import SYSTEM_PROMPT
from prometheus.tools import all_tools
from shared.configuration import Configuration
from shared.llm import get_llm
from shared.memory import get_checkpointer, get_store


# ── State ──────────────────────────────────────────────────────────────
class State(MessagesState):
    summary: str


# ── Nodes ──────────────────────────────────────────────────────────────
def assistant(state: State, config: RunnableConfig, store: BaseStore):
    """Invoke LLM with tools, injecting system prompt + user memory."""
    conf = Configuration.from_runnable_config(config)
    llm = get_llm(model=conf.model_name)
    llm_with_tools = llm.bind_tools(all_tools)

    # Retrieve user memory from Store
    user_id = conf.user_id
    namespace = ("compliance_profile", user_id)
    existing = store.search(namespace)
    memory_ctx = "\n".join(m.value.get("content", "") for m in existing)

    # Build system message
    summary = state.get("summary", "")
    parts = [SYSTEM_PROMPT]
    if memory_ctx:
        parts.append(f"\nUser context from previous sessions:\n{memory_ctx}")
    if summary:
        parts.append(f"\nConversation summary so far:\n{summary}")

    sys_msg = SystemMessage(content="\n".join(parts))
    response = llm_with_tools.invoke([sys_msg] + state["messages"])
    return {"messages": [response]}


def write_memory(state: State, config: RunnableConfig, store: BaseStore):
    """Extract and persist user facts (company, jurisdiction, AI systems)."""
    conf = Configuration.from_runnable_config(config)
    user_id = conf.user_id
    namespace = ("compliance_profile", user_id)

    llm = get_llm(model=conf.model_name)
    extract_prompt = (
        "Extract key facts about the user's organization from this conversation: "
        "industry, jurisdiction, types of AI systems, data processing activities, "
        "compliance maturity. Return a brief paragraph. "
        "If there are no new facts, reply 'No new facts'."
    )
    result = llm.invoke(
        [SystemMessage(content=extract_prompt)] + state["messages"][-6:]
    )
    if "no new facts" not in result.content.lower():
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
            "Extend the summary with the new messages above:"
        )
    else:
        prompt = "Create a concise summary of the conversation above:"

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

# Compile with memory backends
graph = builder.compile(
    checkpointer=get_checkpointer(),
    store=get_store(),
)
