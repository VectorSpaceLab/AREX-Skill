---
name: evaluation
description: "Routes Chinese-LLaMA-Alpaca-2 C-Eval, CMMLU, and LongBench
  evaluation workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# evaluation

Use this sub-skill when the task is about benchmark evaluation, result files, or benchmark-specific prompt/scoring logic.

## Use it when

- the user mentions C-Eval, CMMLU, LongBench, LongBench-E, or benchmark result JSON/CSV files
- the task is about `few_shot`, `cot`, `with_prompt`, `constrained_decoding`, or per-subject accuracy
- the task needs LongBench prediction and scoring behavior
- the user asks how to interpret summary files produced by the repo scripts

## Workflow

1. Read `references/workflows.md` to select C-Eval, CMMLU, LongBench prediction, or LongBench scoring.
2. Confirm the expected benchmark data layout and model path before running a heavy evaluation.
3. Use a fresh output directory per evaluation run.
4. Read `references/troubleshooting.md` if data directories, subject metadata, prompt config, or output files are missing.

## Bundled runtime files

- `scripts/ceval/eval.py`
- `scripts/ceval/evaluator.py`
- `scripts/ceval/llama_evaluator.py`
- `scripts/ceval/subject_mapping.json`
- `scripts/cmmlu/eval.py`
- `scripts/cmmlu/evaluator.py`
- `scripts/cmmlu/llama2_evaluator.py`
- `scripts/cmmlu/categories.py`
- `scripts/longbench/pred_llama2.py`
- `scripts/longbench/eval.py`
- `scripts/longbench/metrics.py`
- `scripts/longbench/config/`
- `scripts/attn_and_long_ctx_patches.py`

## What to read first

- `references/workflows.md` for benchmark-specific command shapes and output files
- `references/troubleshooting.md` for data layout and optional dependency issues

## Routing notes

- Use this sub-skill for benchmark execution and scoring only.
- Use `hf-inference` for ad hoc generation outside the benchmark scripts.
- Use `train-and-merge` if the user first needs to produce or merge the model being evaluated.
