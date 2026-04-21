# Arquimedes fine-tuning pipeline

End-to-end LoRA fine-tuning of a small instruction model on GSM8K so the
Arquimedes tutor has a dedicated math word-problem solver.

## TL;DR

```bash
# 1. prep a local copy of the dataset (optional — notebook also streams)
python -m arquimedes.finetuning.dataset_prep --out data/ft/train.jsonl
python -m arquimedes.finetuning.dataset_prep --split eval --out data/ft/eval.jsonl

# 2. open the notebook in Colab or RunPod (GPU required)
#    arquimedes/finetuning/train_lora.ipynb
#    Set HF_TOKEN + HF_USER in the runtime secrets before the "Push to Hub" cell.

# 3. evaluate base vs. adapter (run on the GPU box after training)
python -m arquimedes.finetuning.eval --model Qwen/Qwen2.5-1.5B-Instruct --limit 300
python -m arquimedes.finetuning.eval --model Qwen/Qwen2.5-1.5B-Instruct \
       --adapter $HF_USER/arquimedes-math-lora --limit 300

# 4. plug the adapter into the live agent
echo "HF_FINETUNED_REPO=$HF_USER/arquimedes-math-lora" >> .env
```

Once `HF_FINETUNED_REPO` is set, the `solve_with_finetuned` tool in
`arquimedes/tools/finetuned_solver.py` becomes callable by the agent.

## Hyperparameters

All tuning knobs live in `config.yaml`. Key choices:

| Knob | Value | Why |
|---|---|---|
| base model | `Qwen/Qwen2.5-1.5B-Instruct` | Fits on a T4 in 4-bit; solid math ability. |
| quantisation | 4-bit NF4 (QLoRA) | Minimum VRAM footprint with negligible accuracy hit. |
| LoRA rank | `r=16`, `alpha=32` | Standard configuration for GSM8K-scale fine-tunes. |
| target modules | `q/k/v/o_proj` | Attention heads are the biggest lever; MLP targets add little. |
| epochs | 1 | With 5 000 examples + LoRA, more epochs overfit the answer format. |
| seq length | 1024 | Captures every GSM8K example without truncation. |
| eval | GSM8K test, first 300 | Exact-match on `#### <number>` regex. |

## Evaluation harness

`eval.py` loads (base ± adapter) and runs greedy decoding over the first
`--limit` problems of `openai/gsm8k` test split. It extracts the final
numeric answer with `####\s*(-?\d+(?:\.\d+)?)` and reports accuracy.

Output shape: `eval_report.json`

```json
{
  "model": "Qwen/Qwen2.5-1.5B-Instruct",
  "adapter": "user/arquimedes-math-lora",
  "n": 300,
  "accuracy": 0.XXX,
  "details": [...]
}
```

## Runtime inference modes

`solve_with_finetuned` tries three strategies in order:

1. **Local GPU** (`transformers` + `peft` + `bitsandbytes`). Fastest when
   the server has CUDA. Disabled automatically on CPU-only hosts unless
   `FT_DEVICE=cpu` is set.
2. **HuggingFace Inference API** (`huggingface_hub.InferenceClient`).
   Serverless — no GPU on the app server. Good for interview demos
   running on a small VPS.
3. **Graceful fallback** — returns an explicit "not configured" message so
   the orchestrator can route to SymPy or to plain LLM reasoning.

## Risk mitigations

- **Training fails / no GPU available**: point `HF_FINETUNED_REPO` at a
  pre-trained public adapter instead (e.g. an existing MAmmoTH LoRA).
  The app is agnostic to who trained the adapter.
- **Adapter drifts vs base model**: evaluate every change with
  `eval.py`; ship only when accuracy improves *and* formatting is stable.
- **Hallucinated final numbers**: the eval regex catches drift early;
  consider chaining with `solve_symbolic` for verification.

## License & ethics

- GSM8K is MIT-licensed.
- Qwen2.5 1.5B Instruct is Apache-2.0.
- Publish the adapter publicly only if you trained on public data. Keep
  any company-internal math benchmarks out of the public Hub repo.
