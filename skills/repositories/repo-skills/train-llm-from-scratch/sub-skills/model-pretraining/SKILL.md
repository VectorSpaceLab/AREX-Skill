---
name: model-pretraining
description: "Guide architecture inspection and base-model pretraining from
  scratch for train-llm-from-scratch, covering the custom decoder-only
  Transformer, modern DDP/bf16 pretraining, legacy single-GPU training,
  checkpoints, memory planning, and smoke configs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Model Pretraining

Use this sub-skill when the task is to inspect the repo's decoder-only Transformer, plan a base-model pretraining run from scratch, build a safe pretraining command, or troubleshoot model/pretraining checkpoints and memory.

## Route Elsewhere

| Request | Route |
|---|---|
| SFT, reward model, DPO/ORPO/KTO, PPO, GRPO/RLVR | `../post-training-rlhf/SKILL.md` |
| Creating or validating HDF5/JSONL datasets | `../data-preparation/SKILL.md` |
| GSM8K evaluation, chat, raw generation UX | `../evaluation-chat/SKILL.md` |
| Streamlit forms, config UI, job manager behavior | `../configuration-ui/SKILL.md` |

## Operating Flow

1. For architecture questions, load `references/model-architecture.md` first and use the constructor/method contracts exactly.
2. Before any expensive run, prove the model import and tiny loss path with `scripts/smoke_transformer.py`.
3. For modern base pretraining, use `references/pretraining-workflows.md` and generate a dry-run command with `scripts/build_pretrain_command.py --mode modern`.
4. For the legacy single-GPU trainer, use `references/legacy-training.md` and generate a dry-run command with `scripts/build_pretrain_command.py --mode legacy`.
5. For failures, load `references/troubleshooting.md`; do not guess around checkpoint shapes, missing token files, DDP launch state, or memory limits.

## Bundled Tools

| Tool | Purpose | Safety |
|---|---|---|
| `scripts/build_pretrain_command.py` | Prints one modern or legacy pretraining command; supports smoke config and repeated extra flags. | Dry-run only; never executes training. |
| `scripts/smoke_transformer.py` | Instantiates a tiny Transformer and runs one CPU or CUDA forward/loss. | No dataset, network, checkpoint write, or optimizer step. |

## Guardrails

- Do not start full pretraining until the user has confirmed data paths, checkpoint output path, device/backend, and wall-time budget.
- Treat base-model pretraining as data-dependent: the token HDF5 files must contain a flat `tokens` dataset and enough tokens for the configured context and batch.
- Prefer the modern workflow for new base checkpoints; use the legacy workflow only when the task specifically needs its single-GPU config, memory flags, or checkpoint helper behavior.
- Keep generated commands repo-relative and user-editable. Do not bake in local checkout paths, private Python executables, or machine-specific storage defaults.
