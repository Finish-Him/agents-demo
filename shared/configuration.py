import os
from dataclasses import dataclass, fields
from typing import Optional
from langchain_core.runnables import RunnableConfig


@dataclass(kw_only=True)
class Configuration:
    """Configurable fields exposed to LangGraph Studio and API."""

    user_id: str = "default-user"
    model_name: str = os.getenv("DEFAULT_MODEL", "deepseek/deepseek-chat-v3-0324")

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> "Configuration":
        configurable = (
            config["configurable"] if config and "configurable" in config else {}
        )
        values = {
            f.name: os.environ.get(f.name.upper(), configurable.get(f.name))
            for f in fields(cls)
            if f.init
        }
        return cls(**{k: v for k, v in values.items() if v})
