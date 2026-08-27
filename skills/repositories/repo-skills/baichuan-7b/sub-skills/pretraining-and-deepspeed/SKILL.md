---
name: pretraining-and-deepspeed
description: "Prepare and preflight Baichuan-7B pretraining corpora, tokenizer
  placement, DeepSpeed host/config files, launch command rendering, and
  checkpoint expectations without executing training."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Baichuan-7B Pretraining and DeepSpeed

Use this sub-skill when the task is about Baichuan-7B pretraining setup, corpus sharding, `tokenizer.model` placement, DeepSpeed JSON/hostfile validation, rendering the training launch command, checkpoint output expectations, or troubleshooting a failed training launch.

Do **not** use this sub-skill for C-Eval/MMLU benchmark execution or architecture-only inference. Route architecture and model internals questions to `../architecture-and-loading/`; route shared package/API and install issues to the root skill's `../../references/api-reference.md` and `../../references/troubleshooting.md`.

## Operating contract

- Treat the original `train.py` as a **launch script**, not an importable API. It parses arguments and initializes distributed DeepSpeed at module import time.
- Use bundled helpers for safe preflight work:
  - `scripts/validate_training_inputs.py` checks corpus, tokenizer, hostfile, DeepSpeed JSON, and checkpoint path layout.
  - `scripts/render_deepspeed_command.py` renders a `deepspeed ... train.py ...` command without running it.
- Never execute DeepSpeed training unless the user explicitly asks to run it and provides suitable GPU/cluster resources, training data, tokenizer, and runtime environment.
- Keep full training claims bounded: bundled helpers validate inputs and render commands only; DeepSpeed training itself is not run by default.

## Fast routing

| User intent | Read first | Action |
|---|---|---|
| "Prepare Baichuan pretraining data" | `references/workflows.md` | Confirm UTF-8 shard files, shard count as a multiple of total ranks, and tokenizer placement; run `validate_training_inputs.py`. |
| "Validate DeepSpeed settings" | `references/configuration.md` | Parse JSON and hostfile; check ZeRO/bf16/micro-batch expectations; report cluster/resource assumptions. |
| "Render/train command" | `references/workflows.md` | Use `render_deepspeed_command.py`; show the command and warnings, do not launch by default. |
| "Where do checkpoints go?" | `references/workflows.md` | Explain `checkpoint_saving_path` and `Epoch-N` tag expectations from `model_engine.save_checkpoint(...)`. |
| "Training launch failed" | `references/troubleshooting.md` | Match the symptom to missing tokenizer/data, malformed hostfile/config, dependency pins, or GPU/cluster issues. |

## Required user inputs for preflight

Ask for or infer these paths from the user's active training workspace:

- Corpus directory, defaulting to `data_dir` in the Baichuan demo.
- SentencePiece tokenizer path, defaulting to `tokenizer.model`.
- DeepSpeed JSON config path, defaulting to `config/deepspeed.json`.
- DeepSpeed hostfile path, defaulting to `config/hostfile`.
- Training entrypoint path if rendering a command, commonly `train.py` in an active checkout or equivalent copied training script.
- Checkpoint output directory, defaulting to `checkpoints`.
- Expected total rank count when the hostfile is unavailable.

## Evidence distilled

This sub-skill is based on the Baichuan-7B training sections in the Chinese and English READMEs, `train.py`, `config/deepspeed.json`, `config/hostfile`, `scripts/train.sh`, and `requirements.txt`. Treat exact `deepspeed==0.9.2`, `torch==2.0.0`, `transformers==4.29.1`, `xformers==0.0.20`, and `sentencepiece==0.1.97` compatibility as a runtime environment concern; the bundled helpers validate layout/configuration and do not prove a full GPU training launch.
