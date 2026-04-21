"""Evaluate base vs. fine-tuned adapter on GSM8K test split.

Extracts the final ``#### <number>`` token from each generation and
compares to the reference answer for exact-match accuracy.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


_ANSWER_RE = re.compile(r"####\s*(-?\d+(?:\.\d+)?)")


def extract_number(text: str) -> str | None:
    m = _ANSWER_RE.search(text.replace(",", ""))
    return m.group(1) if m else None


def evaluate(model_id: str, adapter_id: str | None, limit: int = 50) -> dict:
    """Run the base model (optionally with a LoRA adapter) on GSM8K test."""
    # All heavy deps imported lazily so the module is importable on CPU-only boxes.
    import torch
    from datasets import load_dataset
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
        device_map="auto",
    )
    if adapter_id:
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, adapter_id)

    ds = load_dataset("openai/gsm8k", "main", split=f"test[:{limit}]")

    hits = 0
    details: list[dict] = []
    for row in ds:
        prompt = (
            "You are Archimedes, a math-for-ML tutor. Solve the problem "
            "step by step and end with a line '#### <answer>'.\n\n"
            f"Problem: {row['question']}\n\nSolution:"
        )
        inputs = tok(prompt, return_tensors="pt").to(model.device)
        out = model.generate(
            **inputs,
            max_new_tokens=256,
            do_sample=False,
            temperature=0.0,
            pad_token_id=tok.eos_token_id,
        )
        text = tok.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
        pred = extract_number(text)
        target = extract_number(row["answer"])
        ok = pred is not None and target is not None and pred.strip() == target.strip()
        hits += int(ok)
        details.append({"pred": pred, "target": target, "ok": ok})
    accuracy = hits / len(ds)
    return {
        "model": model_id,
        "adapter": adapter_id,
        "n": len(ds),
        "accuracy": accuracy,
        "details": details,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="Qwen/Qwen2.5-1.5B-Instruct")
    parser.add_argument("--adapter", default=None)
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--out", default="arquimedes/finetuning/eval_report.json")
    args = parser.parse_args()

    report = evaluate(args.model, args.adapter, limit=args.limit)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(report, indent=2))
    print(
        f"accuracy={report['accuracy']:.3f} ({int(report['accuracy']*report['n'])}/{report['n']})"
    )


if __name__ == "__main__":
    main()
