"""Tests for arquimedes/tools/finetuned_solver.py — no GPU required."""

import os
from unittest.mock import patch

from arquimedes.tools import solve_with_finetuned


class TestFinetunedSolver:
    def test_not_configured_returns_explicit_message(self):
        with patch.dict(os.environ, {"HF_FINETUNED_REPO": ""}, clear=False):
            r = solve_with_finetuned.invoke({"question": "What is 17 * 23?"})
        assert "not configured" in r.lower() or "HF_FINETUNED_REPO" in r

    def test_local_unavailable_falls_back_to_inference_api(self):
        """When local CUDA is not available, the tool should try the HF API."""
        from arquimedes.tools import finetuned_solver as fs

        with patch.dict(os.environ, {"HF_FINETUNED_REPO": "fake/adapter"}, clear=False):
            with patch.object(fs, "_solve_local", return_value=None):
                with patch.object(
                    fs, "_solve_inference_api", return_value="[HF Inference API: fake/adapter]\n\n42"
                ):
                    r = solve_with_finetuned.invoke({"question": "What is 17 * 23?"})
        assert "HF Inference API" in r

    def test_both_paths_fail_returns_honest_message(self):
        from arquimedes.tools import finetuned_solver as fs

        with patch.dict(os.environ, {"HF_FINETUNED_REPO": "fake/adapter"}, clear=False):
            with patch.object(fs, "_solve_local", return_value=None):
                with patch.object(fs, "_solve_inference_api", return_value=None):
                    r = solve_with_finetuned.invoke({"question": "What is 17 * 23?"})
        assert "unavailable" in r.lower()


class TestEvalHelpers:
    def test_extract_number(self):
        from arquimedes.finetuning.eval import extract_number
        assert extract_number("Solution ... #### 42") == "42"
        assert extract_number("Many steps.\n#### -7.5") == "-7.5"
        assert extract_number("no final tag here") is None
        # Commas stripped so currency-style answers still parse.
        assert extract_number("#### 1,234") == "1234"
