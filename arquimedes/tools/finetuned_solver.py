"""Tool that calls a fine-tuned LoRA adapter for structured math solutions.

Three runtime modes, in order of preference:

1. **Local GPU** — ``transformers`` + ``peft`` load
   ``HF_FINETUNED_REPO`` on top of its base model. Fastest when the host
   has CUDA; skipped automatically on CPU-only boxes unless
   ``FT_DEVICE=cpu`` is set.
2. **HF Inference API** — serverless call to the adapter repo via
   ``huggingface_hub.InferenceClient``. No GPU needed; pay-per-call.
3. **Graceful fallback** — when no adapter is configured or both paths
   fail, the tool returns an honest "not configured" message so the
   orchestrator can route to another solver (SymPy, LLM reasoning).

The tutor calls this for GSM8K-style word problems where a dedicated
math-solver is more reliable than the general-purpose chat model.
"""

from __future__ import annotations

import os
from functools import lru_cache

from langchain_core.tools import tool


PROMPT_TEMPLATE = (
    "You are Archimedes, a math-for-ML tutor. Solve the following problem "
    "step by step and end with a line '#### <final_numeric_answer>'.\n\n"
    "Problem: {question}\n\nSolution:"
)


def _ft_device() -> str:
    return os.getenv("FT_DEVICE", "auto")


@lru_cache(maxsize=1)
def _load_local_pipeline(adapter_repo: str):
    """Cached loader for the local GPU path. Returns ``None`` on failure."""
    try:
        import torch
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except Exception:
        return None

    device = _ft_device()
    if device == "auto":
        if not torch.cuda.is_available():
            return None  # fall through to Inference API
    elif device == "cpu" and not torch.cuda.is_available():
        pass  # explicitly allowed CPU
    elif device == "cuda" and not torch.cuda.is_available():
        return None

    # Adapter config tells us which base to load underneath.
    try:
        from peft import PeftConfig
        cfg = PeftConfig.from_pretrained(adapter_repo, token=os.getenv("HF_TOKEN"))
        base = cfg.base_model_name_or_path
    except Exception:
        base = os.getenv("FT_BASE_MODEL", "Qwen/Qwen2.5-1.5B-Instruct")

    try:
        tok = AutoTokenizer.from_pretrained(base, token=os.getenv("HF_TOKEN"))
        model = AutoModelForCausalLM.from_pretrained(
            base,
            torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None,
            token=os.getenv("HF_TOKEN"),
        )
        model = PeftModel.from_pretrained(model, adapter_repo, token=os.getenv("HF_TOKEN"))
        return tok, model
    except Exception:
        return None


def _solve_local(question: str, adapter_repo: str) -> str | None:
    loaded = _load_local_pipeline(adapter_repo)
    if loaded is None:
        return None
    tok, model = loaded
    prompt = PROMPT_TEMPLATE.format(question=question)
    import torch
    inputs = tok(prompt, return_tensors="pt").to(model.device)
    out = model.generate(
        **inputs,
        max_new_tokens=256,
        do_sample=False,
        pad_token_id=tok.eos_token_id,
    )
    completion = tok.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
    return f"[local adapter: {adapter_repo}]\n\n{completion.strip()}"


def _solve_inference_api(question: str, adapter_repo: str) -> str | None:
    try:
        from huggingface_hub import InferenceClient
    except Exception:
        return None

    token = os.getenv("HF_TOKEN")
    if not token:
        return None

    client = InferenceClient(model=adapter_repo, token=token)
    prompt = PROMPT_TEMPLATE.format(question=question)
    try:
        out = client.text_generation(
            prompt,
            max_new_tokens=256,
            temperature=0.01,
            return_full_text=False,
        )
    except Exception as e:
        return f"(HF Inference API unavailable: {e})"
    return f"[HF Inference API: {adapter_repo}]\n\n{out.strip()}"


@tool
def solve_with_finetuned(question: str) -> str:
    """Solve a math word problem using the fine-tuned LoRA adapter.

    Prefer this for GSM8K-style arithmetic / word problems where a
    dedicated math solver is more reliable than chat-style reasoning.
    Falls back to HuggingFace Inference API if no local GPU is present.

    Args:
        question: The math problem in natural language.
    """
    adapter = os.getenv("HF_FINETUNED_REPO", "").strip()
    if not adapter:
        return (
            "(solve_with_finetuned is not configured: set HF_FINETUNED_REPO to "
            "the HF Hub id of a LoRA adapter trained on GSM8K. See "
            "arquimedes/finetuning/README.md)"
        )

    local = _solve_local(question, adapter)
    if local is not None:
        return local
    remote = _solve_inference_api(question, adapter)
    if remote is not None:
        return remote
    return (
        f"(fine-tuned solver unavailable — local GPU path disabled and "
        f"HF Inference API call failed for adapter {adapter})"
    )


finetuned_tools = [solve_with_finetuned]
