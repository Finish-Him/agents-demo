"""Load GSM8K and format it as chat-style (prompt, completion) pairs.

Can be run as a script::

    python -m arquimedes.finetuning.dataset_prep --out data/ft/gsm8k.jsonl

or imported by the training notebook.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

import yaml

CONFIG_PATH = Path(__file__).parent / "config.yaml"


def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def _format_example(question: str, answer: str, template: str) -> dict:
    prompt = template.format(question=question.strip())
    return {"prompt": prompt, "completion": answer.strip()}


def build_records(split: str = "train", limit: int | None = None) -> Iterable[dict]:
    from datasets import load_dataset  # imported lazily — heavy dep

    cfg = load_config()
    ds_name = cfg["dataset"]["name"]
    ds_config = cfg["dataset"]["config"]
    template = cfg["dataset"]["prompt_template"]
    target = cfg["dataset"]["target_field"]

    split_spec = cfg["dataset"][f"{split}_split"]
    ds = load_dataset(ds_name, ds_config, split=split_spec)
    for i, row in enumerate(ds):
        if limit is not None and i >= limit:
            break
        yield _format_example(row["question"], row[target], template)


def dump_jsonl(records: Iterable[dict], path: str | Path) -> int:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n += 1
    return n


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", default="train", choices=["train", "eval"])
    parser.add_argument("--out", default="data/ft/gsm8k.jsonl")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    n = dump_jsonl(build_records(args.split, args.limit), args.out)
    print(f"wrote {n} records to {args.out}")


if __name__ == "__main__":
    main()
