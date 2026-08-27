---
name: "qwen-vl-series-finetune"
description: "Route Qwen-VL-series multimodal fine-tuning, preference training,
  classification, adapter merge, and Gradio serving tasks."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Qwen-VL Series Finetune

Use this repo skill for the public Qwen-VL-series training repo that fine-tunes Qwen2-VL, Qwen2.5-VL, Qwen3-VL, and Qwen3.5 multimodal models with Hugging Face, DeepSpeed, PEFT, TRL, and Liger.

This skill is a router, not a monolithic manual. Start here, then follow the sub-skill that matches the user request.

## What this skill covers

- Multimodal dataset preparation and validation for SFT, DPO, GRPO, and classification.
- Supervised fine-tuning, including full finetuning, LoRA, vision LoRA, video training, and evaluation during training.
- Preference training with DPO and GRPO, including reasoning fields and Liger GRPO options.
- Sequence classification training, custom heads, class-imbalance losses, and early stopping.
- Adapter merging and Gradio inference for merged or adapter-backed models.

## Route map

- `sub-skills/data-and-multimodal/` — build or validate JSON datasets, image/video path handling, token formatting, and reasoning fields.
- `sub-skills/sft-training/` — full SFT, LoRA/QLoRA, vision LoRA, video finetuning, and DeepSpeed launch planning.
- `sub-skills/preference-training/` — DPO and GRPO workflows, reward functions, and reasoning-aware preference data.
- `sub-skills/classification-training/` — sequence classification labels, losses, metrics, and early stopping.
- `sub-skills/serving-and-adapters/` — LoRA merge, model loading, and Gradio inference.

## Read first

- `references/install.md` for install and inspection-environment guidance.
- `references/bundled-runtime.md` for the bundled `src/` tree, DeepSpeed configs, and executable training/merge/serving helpers.
- `references/workflow-map.md` for the fastest path from user request to sub-skill.
- `references/data-formats.md` for shared JSON schemas and media/routing rules.
- `references/cli-reference.md` for the main entry points and key flags.
- `references/model-compatibility.md` for model-family and backend caveats.
- `references/troubleshooting.md` for the most common setup and runtime failures.

## Minimal environment check

Before any CUDA-heavy task, run the bundled diagnostic:

- `scripts/check_environment.py`

Use it to confirm package imports, CUDA visibility, and optional serving dependencies without downloading weights or datasets.

## Operating rules

- Keep runtime paths inside this skill tree; do not point future agents back to the source checkout.
- Use the bundled `src/` entrypoints and DeepSpeed configs here; command helpers run from the skill root and set `PYTHONPATH=src`.
- Use the bundled scripts and references here instead of the original repo launch scripts.
- Treat CPU help/import checks as valid only for parser, schema, and pure-Python utilities.
- Treat actual training, multimodal generation, Gradio serving, and adapter merge as CUDA workflows.
- For Qwen3.5, prefer `--disable_flash_attn2 True` unless the user explicitly needs another backend.
- For video workflows, prefer the PyAV/FFmpeg path documented in the references and treat `fps`/`nframes` as mutually exclusive.

## Good first questions

If the user asks for something broad, ask which workflow they want:

- data preparation or validation
- supervised finetuning
- DPO or GRPO
- classification training
- merge or serve

If the user already named one of those workflows, jump directly to that sub-skill.

## Provenance and router metadata

- `references/repo-provenance.md` records the source checkout state.
- `references/repo-routing-metadata.json` records the managed router placement used by import tooling.

## Safe default

If the user asks for a command, prefer a dry-run or command-builder script first, then the execution command after the data, model, and backend assumptions are explicit.
