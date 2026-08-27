---
name: training-recipes
description: "Diffusers training recipes for DreamBooth, LoRA, textual
  inversion, ControlNet, text-to-image, T2I-Adapter, InstructPix2Pix, SDXL,
  Flux, and SD3 examples with dataset and Accelerate safety checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Diffusers Training Recipes

Use this sub-skill when the task is to prepare or adapt Diffusers training examples, build an `accelerate launch` command, validate a local image dataset, choose between DreamBooth/LoRA/textual inversion/ControlNet/T2I-Adapter/text-to-image recipes, or debug training setup failures.

Route elsewhere:
- Inference-only pipeline usage, loading trained adapters, or generation scripts: use `pipelines-and-inference`.
- Maintainer test policy, copied-code updates, or conversion PR mechanics: use `conversion-and-maintenance`.

## Fast Path

1. Identify the recipe and base family from the user request: SD 1.x/2.x, SDXL, SD3, Flux, or a task-specific adapter.
2. Validate local datasets before composing commands:
   - `python sub-skills/training-recipes/scripts/dataset_layout_check.py --data-dir DATA --require-captions`
   - Add `--conditioning-dir COND` for ControlNet/T2I-Adapter/Flux control image pairs.
3. Generate a dry-run command rather than launching training:
   - `python sub-skills/training-recipes/scripts/training_command_builder.py --recipe dreambooth-lora --model MODEL --dataset DATA --output-dir OUT --instance-prompt "a photo of sks dog"`
4. Add memory controls before suggesting real runs: `--mixed_precision`, `--gradient_checkpointing`, small `--train_batch_size`, `--gradient_accumulation_steps`, checkpointing, and a capped `--max_train_steps`.
5. Require explicit user confirmation before running expensive training, Hub pushes, remote downloads of gated models, or commands that overwrite a non-empty output directory.

## References

- Recipe selection and command patterns: [references/recipes.md](references/recipes.md)
- Dataset formats and validation: [references/datasets-and-launch.md](references/datasets-and-launch.md)
- Troubleshooting training failures: [references/troubleshooting.md](references/troubleshooting.md)

## Bundled Helpers

- `scripts/training_command_builder.py` prints safe `accelerate launch` commands for common recipes without importing Diffusers or starting training.
- `scripts/dataset_layout_check.py` validates tiny local imagefolder layouts, optional captions, metadata files, and conditioning-image pair counts.
