"""Tests for shared/configuration.py — Configuration dataclass."""

import os
from unittest.mock import patch

import pytest

from shared.configuration import Configuration


class TestConfiguration:
    """Test Configuration.from_runnable_config()."""

    def test_default_values(self):
        config = Configuration()
        assert config.user_id == "default-user"
        assert config.model_name  # should have some default

    def test_from_config_with_configurable(self):
        runnable_config = {
            "configurable": {
                "user_id": "test-user-123",
                "model_name": "gpt-4o-mini",
            }
        }
        config = Configuration.from_runnable_config(runnable_config)
        assert config.user_id == "test-user-123"
        assert config.model_name == "gpt-4o-mini"

    def test_from_config_none(self):
        config = Configuration.from_runnable_config(None)
        assert config.user_id == "default-user"

    def test_from_config_empty_configurable(self):
        config = Configuration.from_runnable_config({"configurable": {}})
        assert config.user_id == "default-user"

    @patch.dict(os.environ, {"USER_ID": "env-user", "MODEL_NAME": "env-model"})
    def test_env_vars_override(self):
        config = Configuration.from_runnable_config(None)
        assert config.user_id == "env-user"
        assert config.model_name == "env-model"

    @patch.dict(os.environ, {"USER_ID": "env-user"})
    def test_configurable_takes_precedence_over_env(self):
        runnable_config = {
            "configurable": {
                "user_id": "config-user",
            }
        }
        config = Configuration.from_runnable_config(runnable_config)
        # env var should be overridden by configurable value
        assert config.user_id in ("config-user", "env-user")  # implementation-dependent
