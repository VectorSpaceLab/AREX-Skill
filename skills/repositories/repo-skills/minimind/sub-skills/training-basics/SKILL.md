---
name: training-basics
description: "Enables future agents to prepare MiniMind training data and
  operate tokenizer, pretraining, SFT, LoRA, checkpoint, DDP, and tiny
  validation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MiniMind Training Basics

Use this sub-skill when the task is to prepare MiniMind training data, choose core model/training knobs, start or resume pretraining, run full supervised fine-tuning, run LoRA fine-tuning, validate tokenizer/data compatibility, or perform a safe tiny training smoke.

## Load order

- For JSONL schemas, tokenizer special tokens, chat-template behavior, tool-call fields, and reasoning fields, read [references/data-formats.md](references/data-formats.md).
- For tokenizer, pretraining, full SFT, LoRA, DDP, checkpoint resume, logging, mixed-precision, gradient accumulation, and compile command routes, read [references/workflows.md](references/workflows.md).
- For `MiniMindConfig`, `MiniMindForCausalLM`, model-size knobs, RoPE/YaRN context, output weight names, checkpoint state, and LoRA merge semantics, read [references/model-and-checkpoints.md](references/model-and-checkpoints.md).
- For missing files, invalid JSONL, tokenizer mismatch, missing weights, LoRA compile incompatibility, device choice, resume, logging, and output-directory failures, read [references/troubleshooting.md](references/troubleshooting.md).

## Bundled safe helpers

- Validate pretrain/SFT JSONL and optional local tokenizer compatibility with [scripts/validate_minimind_jsonl.py](scripts/validate_minimind_jsonl.py).
- Run a bounded random-tensor model forward/backward/generate smoke with [scripts/tiny_training_smoke.py](scripts/tiny_training_smoke.py).

Both helpers are deterministic by default, perform no downloads, do not require credentials, and do not launch full training.

## Boundaries

This sub-skill owns the core MiniMind training path: tokenizer validation/training settings, pretrain JSONL, SFT conversation JSONL, pretraining, full SFT, LoRA SFT, checkpoint resume, DDP launch, data/model configuration, and tiny validation.

Route API servers, web UI, local chat, tool-call evaluation, model export, and merged-weight serving to the `inference-serving` sub-skill. Route DPO, distillation, PPO, GRPO/CISPO, and Agentic RL to the `rlhf-agentic` sub-skill.
