"""Reusable LCEL chains for Arquimedes.

Each factory returns a LangChain runnable that can be composed further
(e.g. `chain.invoke({...})`, `chain.stream({...})`, `chain.batch([...])`).
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from arquimedes.prompts import SYSTEM_PROMPT
from arquimedes.schemas import RouterDecision, StudentProfileUpdate
from arquimedes.tools import all_tools
from shared.llm import get_llm


# ── Assistant chain ────────────────────────────────────────────────────────
def build_assistant_chain(model: str | None = None, extra_context: str = ""):
    """Primary teaching chain.

    Pattern: ChatPromptTemplate | llm.bind_tools(all_tools).
    `extra_context` is appended to the system message (used to inject the
    student profile and conversation summary from the graph state).
    """
    sys = SYSTEM_PROMPT + ("\n\n" + extra_context if extra_context else "")
    prompt = ChatPromptTemplate.from_messages(
        [("system", sys), MessagesPlaceholder(variable_name="messages")]
    )
    llm = get_llm(model=model).bind_tools(all_tools)
    return prompt | llm


# ── Router chain ───────────────────────────────────────────────────────────
_ROUTER_SYS = """\
You are a routing classifier for a math-for-ML tutor agent.

Given the most recent learner message and the latest assistant response, decide
what should happen next:

- 'rag'    : learner asks something factual/citation-seeking that benefits from
             retrieving passages from the math knowledge base (textbook quotes,
             chapter references, rigorous definitions).
- 'tools'  : the assistant already emitted tool_calls in its last response.
- 'direct' : plain pedagogical turn — proceed to memory extraction / end.

Reply with the structured decision only.
"""


def build_router_chain(model: str | None = None):
    prompt = ChatPromptTemplate.from_messages(
        [("system", _ROUTER_SYS), MessagesPlaceholder(variable_name="messages")]
    )
    llm = get_llm(model=model).with_structured_output(RouterDecision)
    return prompt | llm


# ── Memory extractor chain ─────────────────────────────────────────────────
_MEMORY_SYS = """\
Analyze the recent conversation and extract atomic facts about the student:
their level per topic, strengths, weaknesses, progress signals. One fact per
topic. If the last turns contain no new teaching signal (e.g., the student only
said "hi" or asked about logistics), set has_new_information=false and return
an empty facts list.
"""


def build_memory_extractor_chain(model: str | None = None):
    prompt = ChatPromptTemplate.from_messages(
        [("system", _MEMORY_SYS), MessagesPlaceholder(variable_name="messages")]
    )
    llm = get_llm(model=model).with_structured_output(StudentProfileUpdate)
    return prompt | llm
