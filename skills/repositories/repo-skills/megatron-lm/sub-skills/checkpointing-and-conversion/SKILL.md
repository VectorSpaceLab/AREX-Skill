---
name: checkpointing-and-conversion
description: "Work with Megatron distributed checkpoints, safe loading,
  resharding, and GPT-Hybrid conversion."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# checkpointing-and-conversion

Use this sub-skill when the task involves Megatron checkpoint formats, save/load/resume behavior, optimizer state compatibility, distributed checkpoint resharding, PyTorch safe loading, or GPTModel ↔ HybridModel conversion.

## Read first

- For checkpoint formats, optimizer state behavior, async saves, and safe loading, read [references/checkpoint-reference.md](references/checkpoint-reference.md).
- For GPT-to-Hybrid, Hybrid-to-GPT, and Hugging Face/Megatron conversion decision paths, read [references/conversion-workflows.md](references/conversion-workflows.md).
- For failed loads, unsafe globals, unsupported hybrid patterns, missing tracker files, or memory issues, read [references/troubleshooting.md](references/troubleshooting.md).
- Use [scripts/render_gpt_hybrid_conversion_command.py](scripts/render_gpt_hybrid_conversion_command.py) to validate and render a conversion command template without touching checkpoint files.

## Route by task

| Task | Action |
|---|---|
| Resume training from a checkpoint | Confirm `--load`, `--save`, `--ckpt-format`, optimizer load flags, and parallelism compatibility. |
| Change TP/PP/EP/FSDP layout | Prefer distributed checkpoint formats and, for optimizer resharding, fully-reshardable optimizer state. |
| PyTorch 2.6 unsafe global error | Keep safe loading; allow-list only the required class or use the repo's safe globals guidance. |
| GPTModel to HybridModel migration | Choose load-time translation or offline converter; validate `--hybrid-layer-pattern`. |
| HF ↔ Megatron conversion | Treat Megatron Bridge/HF conversion as an external workflow with mounts, tokens, and model-specific scripts. |

## Checkpoint workflow

1. Pull checkpoint metadata first: format, root directory shape, tracker file, model args, parallel sizes, optimizer state format, and target run command.
2. Decide whether the user needs weights-only load, full resume, finetune semantics, or format conversion.
3. If changing parallelism, confirm the checkpoint format and optimizer state format support that change.
4. If migrating GPT to Hybrid, validate the layer pattern before running any conversion.
5. After any conversion or resume, run a bounded smoke before launching full training.

## Boundaries

- Training launch details belong to [../training-cli-and-data/SKILL.md](../training-cli-and-data/SKILL.md).
- Model architecture and parallelism reasoning belongs to [../core-models-and-parallelism/SKILL.md](../core-models-and-parallelism/SKILL.md).
- Inference-time checkpoint use belongs to [../inference-and-serving/SKILL.md](../inference-and-serving/SKILL.md).
