---
name: evaluation-workflows
description: "Prepare and troubleshoot Baichuan-7B C-Eval and MMLU evaluation
  workflows, including safe preflight validation, command rendering, benchmark
  layout requirements, output files, and CUDA/model prerequisites."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Evaluation Workflows

Use this sub-skill when the user asks to evaluate a Baichuan-7B checkpoint on C-Eval or MMLU, validate benchmark inputs before running, construct the native evaluation commands, or interpret the files produced by those benchmark scripts.

## Route here for

- C-Eval command construction around `evaluation/evaluate_zh.py`: `--model_name_or_path`, `--shot`, `--split`, and `--output_dir`.
- MMLU command construction around `evaluation/evaluate_mmlu.py`: `-m/--model`, `-k/--ntrain`, `-d/--data_dir`, and `-s/--save_dir`.
- Safe static preflight of model paths, C-Eval dataset access assumptions, MMLU Hendrycks/test checkout layout, `categories.py`, CSV subject pairing, and CUDA/import prerequisites.
- Explaining C-Eval JSON outputs and MMLU per-subject CSV/result-directory artifacts.
- Benchmark-specific failures such as missing `datasets`, absent MMLU `categories.py`, wrong split names, no CUDA, missing weights/tokenizer files, or MMLU prompts that trigger the 2048-token truncation loop.

## Do not route here for

- Baichuan architecture internals, local class signatures, tiny forward checks, or generation/cache behavior: use sibling [architecture-and-loading](../architecture-and-loading/SKILL.md).
- DeepSpeed pretraining, corpus shard validation, hostfiles, or cluster launch setup: use sibling [pretraining-and-deepspeed](../pretraining-and-deepspeed/SKILL.md).
- Broad package installation or backend issues that are not benchmark-specific: start from the parent root skill and shared [troubleshooting](../../references/troubleshooting.md).

## Operating map

1. For benchmark behavior, command shapes, input layouts, and output artifacts, read [workflows](references/workflows.md).
2. Before running a real benchmark, use the safe bundled preflight helper. It validates inputs and renders commands; it does not load model weights, fetch datasets, or run benchmark inference.
3. For failures, read [local troubleshooting](references/troubleshooting.md), then escalate cross-cutting model-loading issues to [architecture-and-loading](../architecture-and-loading/SKILL.md) or shared [API/troubleshooting](../../references/api-reference.md).
4. Keep full benchmark execution as a user/runtime operation. The bundled checks validate imports, CUDA availability, and static layouts only; they do not run C-Eval or MMLU end to end.

## Safe preflight examples

Validate the C-Eval command shape and prerequisites for a local checkpoint:

```bash
python sub-skills/evaluation-workflows/scripts/check_evaluation_inputs.py ceval \
  --repo-root /path/to/Baichuan-7B \
  --model /path/to/Baichuan-7B-weights \
  --shot 5 \
  --split val \
  --output-dir ceval_output \
  --check-imports \
  --check-cuda
```

Validate a Hendrycks/test MMLU checkout and render the copy/run commands:

```bash
python sub-skills/evaluation-workflows/scripts/check_evaluation_inputs.py mmlu \
  --repo-root /path/to/Baichuan-7B \
  --benchmark-root /path/to/hendrycks-test \
  --model /path/to/Baichuan-7B-weights \
  --data-dir data \
  --save-dir results \
  --ntrain 5 \
  --check-imports \
  --check-cuda
```

The helper is intentionally safe by default: it checks files, imports only when requested, performs a tiny CUDA availability/allocation probe only when requested, and renders the native commands instead of executing them.
