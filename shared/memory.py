from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore

# Singleton instances shared across all agents in the same process
_checkpointer: MemorySaver | None = None
_store: InMemoryStore | None = None


def get_checkpointer() -> MemorySaver:
    global _checkpointer
    if _checkpointer is None:
        _checkpointer = MemorySaver()
    return _checkpointer


def get_store() -> InMemoryStore:
    global _store
    if _store is None:
        _store = InMemoryStore()
    return _store
