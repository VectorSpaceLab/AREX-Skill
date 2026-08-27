---
name: core-training
description: "Plan and validate code-first Unsloth Core model loading, LoRA/full
  finetuning setup, trainer/data preparation, and backend troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Core Training

Use this sub-skill when a user wants a code-first Unsloth Core training plan, import/backend sanity check, model loading choice, LoRA or full-finetuning setup, trainer wiring, chat-template/data preparation, or a tiny configuration/data validation pass.

## Route First

- For `unsloth` command-line orchestration, generated CLI configs, or Studio-free command runs, read `../cli-workflows/SKILL.md`.
- For saving adapters, merged checkpoints, GGUF/16-bit export, or Hub upload after training, read `../model-export/SKILL.md`.
- For Studio web UI training or Studio backend/API behavior, read `../studio-runtime/SKILL.md`.
- Stay here for Python API planning with `FastLanguageModel`, `FastModel`, `FastVisionModel`, `FastTextModel`, `FastSentenceTransformer`, `UnslothTrainer`, chat templates, raw text helpers, and safe preflight checks.

## Read Or Run

- Read `references/api-reference.md` to choose the correct `Fast*` loader, quantization flags, LoRA targets, trainer classes, and chat/data utility APIs.
- Read `references/workflows.md` for code-first QLoRA, full-finetuning, vision, sentence-transformer, raw-text, and planning-only workflow skeletons.
- Read `references/data-formats.md` before shaping JSONL chat, ShareGPT-style, raw text, CSV/JSON, vision, or config files for training.
- Read `references/troubleshooting.md` when imports, optional dependencies, CUDA/MLX routing, tokenizer mappings, data fields, quantization, downloads, or VRAM choices fail.
- Run `scripts/inspect_unsloth_core.py --help` to inspect installed Unsloth Core signatures, package/backend availability, and import errors without loading a model.
- Run `scripts/validate_training_config.py --help` to validate a YAML/JSON training config and optional tiny dataset sample before writing runnable training code.

## Safe Defaults

- Import Unsloth before `transformers`, `trl`, or `peft` so Unsloth can patch training paths before those libraries initialize.
- Treat `load_in_4bit=True` as the QLoRA default for GPU memory savings; set all quantization flags false for full finetuning.
- Use `is_bfloat16_supported()` or `is_bf16_supported()` to pick `bf16=True` versus `fp16=True` in trainer arguments.
- Validate dataset field names and message roles before calling `standardize_sharegpt`, `get_chat_template`, or `SFTTrainer`.
- Do not run model downloads, training, native notebooks, or expensive examples during planning; generate code/configs and run only safe helper checks first.
