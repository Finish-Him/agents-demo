"""Atlas — Tech Stack Specialist Agent.

LangGraph ReAct agent with external API tools (GitHub + HuggingFace),
conversation persistence, and pre-loaded stack knowledge.
Demonstrates: ReAct loop, external API tools, tools_condition, ToolNode.
"""

from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from atlas.prompts import SYSTEM_PROMPT
from atlas.tools import all_tools
from shared.configuration import Configuration
from shared.llm import get_llm
from shared.memory import get_checkpointer, get_store


# ── Nodes ──────────────────────────────────────────────────────────────
def assistant(state: MessagesState, config: RunnableConfig):
    """Invoke LLM with tools bound."""
    conf = Configuration.from_runnable_config(config)
    llm = get_llm(model=conf.model_name)
    llm_with_tools = llm.bind_tools(all_tools)

    sys_msg = SystemMessage(content=SYSTEM_PROMPT)
    response = llm_with_tools.invoke([sys_msg] + state["messages"])
    return {"messages": [response]}


# ── Graph ──────────────────────────────────────────────────────────────
builder = StateGraph(MessagesState, config_schema=Configuration)

builder.add_node("assistant", assistant)
builder.add_node("tools", ToolNode(all_tools))

builder.add_edge(START, "assistant")
builder.add_conditional_edges("assistant", tools_condition)
builder.add_edge("tools", "assistant")

graph = builder.compile(
    checkpointer=get_checkpointer(),
    store=get_store(),
)
