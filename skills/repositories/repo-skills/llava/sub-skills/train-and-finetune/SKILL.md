---
name: train-and-finetune
description: "Guides LLaVA custom training data, pretraining, full fine-tuning,
  LoRA, QLoRA, ScienceQA conversion, DeepSpeed config choice, and checkpoint
  merge or delta utilities."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Train and Finetune

Use this sub-skill when the user needs to prepare LLaVA training data, build pretraining or fine-tuning commands, choose LoRA or QLoRA settings, convert ScienceQA into LLaVA format, or merge/checkpoint projectors and deltas.

## What it covers

- custom LLaVA conversation JSON validation
- pretraining, full fine-tuning, LoRA, QLoRA, and task-specific fine-tuning command templates
- DeepSpeed config selection and the repo's `zero2`, `zero3`, and `zero3_offload` templates
- ScienceQA conversion to LLaVA format
- checkpoint utilities: `merge_lora_weights`, `apply_delta`, `make_delta`, `consolidate`, `extract_mm_projector`

## What it excludes

- Interactive chat and serving workflows belong to `chat-and-serve`.
- Benchmark submission generation and result conversion belong to `evaluate-and-benchmark`.
- Maintainer release/upload tooling is excluded.

## Read these references

- [`references/data-formats.md`](references/data-formats.md) for the training JSON schema and ScienceQA conversion shape.
- [`references/training-workflows.md`](references/training-workflows.md) for command templates and flag guidance.
- [`references/checkpoint-utilities.md`](references/checkpoint-utilities.md) for merge/delta/projector utilities.
- [`references/troubleshooting.md`](references/troubleshooting.md) for the common training and checkpoint failures.

## Bundled scripts

- [`scripts/validate_training_json.py`](scripts/validate_training_json.py) validates a LLaVA training JSON list and catches schema mistakes before launch.
- [`scripts/build_training_command.py`](scripts/build_training_command.py) prints safe command templates for the main training modes.
- `scripts/deepspeed/zero2.json`, `scripts/deepspeed/zero3.json`, and `scripts/deepspeed/zero3_offload.json` are copied templates for DeepSpeed launch commands.

## Typical routing cues

Choose this sub-skill when the user says any of:

- fine-tune LLaVA on my dataset
- prepare LLaVA training JSON
- train a projector or LoRA adapter
- convert ScienceQA to LLaVA format
- merge LoRA weights
- apply delta weights
- consolidate a checkpoint

## Common decision points

1. **Is the task pretraining or instruction fine-tuning?**
   - Use the pretrain template when you are learning a projector from image-text pairs.
   - Use fine-tune or task fine-tune when you already have a projector and LLaVA-style instructions.
2. **Is memory tight?**
   - Use LoRA or QLoRA when you need parameter-efficient tuning.
   - Choose the DeepSpeed config based on whether you need ZeRO-2, ZeRO-3, or CPU offload.
3. **Is the dataset custom?**
   - Validate it first.
   - Make sure the `conversations` list alternates human and gpt turns.
4. **Is the checkpoint an adapter, delta, or projector?**
   - Use the checkpoint utility reference to choose merge, apply_delta, make_delta, or consolidate.

## Troubleshooting snapshot

If training fails, check whether the problem is actually one of these:

- malformed JSON or missing training fields
- `image` paths that do not exist
- wrong `model_base` for a LoRA adapter
- incompatible DeepSpeed config or launcher
- GPU memory shortage or unsupported precision
- PEFT/Accelerate/Transformers version drift
- W&B login or reporting issues
- notebook-style data not converted into LLaVA conversation format
