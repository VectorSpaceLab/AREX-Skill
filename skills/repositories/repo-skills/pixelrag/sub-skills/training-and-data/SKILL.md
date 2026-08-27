---
name: training-and-data
description: "Use PixelRAG's separate training project, released LoRA adapters,
  and synthetic data pipeline guidance safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# PixelRAG Training and Data

Use this sub-skill when the task asks about PixelRAG LoRA fine-tuning, the released screenshot embedding adapter, training/eval datasets, synthetic query generation, hard-negative mining, JSONL formats, or the separate `train/` uv project.

## Start Here

1. Decide whether the user needs the released model or full retraining.
   - For most usage, load the published LoRA adapter instead of retraining.
   - Full retraining is a multi-GPU/data/credential workflow.
2. Remember `train/` is a separate uv project. Do not install it from the root package environment.
3. Confirm resource requirements before running anything heavy: A100/H100-class GPU, large disk, HF datasets, vLLM reader for eval, OpenAI/W&B/Google keys depending on stage.
4. Validate small data samples with [pixelrag_training_data_check.py](scripts/pixelrag_training_data_check.py) before launching generation/training scripts.

## Read or Run

- Read [training-recipe.md](references/training-recipe.md) for environment, released adapter, training command shape, and evaluation expectations.
- Read [data-pipeline.md](references/data-pipeline.md) for synthetic query generation, filters, hard negatives, export/split, and JSONL fields.
- Read [troubleshooting.md](references/troubleshooting.md) for keys, data paths, CUDA, vLLM, W&B, and silent-zero eval failures.
- Run [pixelrag_training_data_check.py](scripts/pixelrag_training_data_check.py) on a JSONL sample before spending GPU/API budget.

## Common Routes

| Request | Action |
| --- | --- |
| "Use the trained PixelRAG embedding" | Load `Chrisyichuan/wiki-screenshot-embedding-lora` adapter on top of `Qwen/Qwen3-VL-Embedding-2B`; no retraining needed. |
| "Reproduce the training run" | Use the separate `train/` uv env, required datasets, vLLM reader, OpenAI grader, and W&B/offline logging plan. |
| "Generate synthetic data" | Follow query generation -> self-contained filter -> hard-negative mining -> VQA false-negative filter -> naturalness scoring -> export/split -> HF packaging. |
| "Debug QA score is zero" | Check OpenAI key/base URL and reader endpoint; training may be fine while eval grading fails. |
| "Evaluate a checkpoint" | Use training eval scripts and route paper-level benchmark comparison to `../evaluation-reproduction/SKILL.md`. |

## Boundaries

- Do not call Google/OpenAI, upload to HF, or start W&B/vLLM/training jobs without explicit user approval.
- Do not mix root PixelRAG package extras with the pinned `train/` project environment.
- Do not claim CPU is a substitute for the training run; CPU may validate JSONL shape but not training performance.
- Keep local data roots, tokens, W&B run URLs, and API keys out of reusable notes unless the user explicitly asks for local operational commands.
