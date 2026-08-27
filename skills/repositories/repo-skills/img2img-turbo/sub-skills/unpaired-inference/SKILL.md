---
name: unpaired-inference
description: "Guide CycleGAN-Turbo unpaired translation with pretrained
  day/night/rain/clear models and custom checkpoints."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Unpaired Inference

Use this sub-skill for CycleGAN-Turbo unpaired image translation when the task is to run or plan inference with:

- pretrained `day_to_night`, `night_to_day`, `clear_to_rainy`, or `rainy_to_clear` models;
- a custom CycleGAN-Turbo checkpoint selected by `--model_path`;
- prompt, direction, image preprocessing, precision, output naming, CUDA, xformers, or checkpoint-download troubleshooting for unpaired translation.

Do not use this sub-skill for Pix2Pix-Turbo paired edge/sketch/custom paired checkpoint inference; route those tasks to `paired-inference`. Do not use it for dataset layout, training, validation metrics, or checkpoint creation; route those tasks to `training`.

## Start here

1. Choose pretrained or custom mode from [CLI and API reference](references/cli-and-api.md).
2. Build a safe command with [the bundled command helper](scripts/build_unpaired_inference_command.py) before running source-checkout inference.
3. Follow a pretrained or custom recipe in [workflows](references/workflows.md).
4. If a run fails before producing the output image, use [troubleshooting](references/troubleshooting.md) to classify the failure before changing prompts, directions, image sizes, or the runtime environment.

## Operating rules

- Pretrained model names already carry their caption and direction in the model constructor; do not pass `--prompt` or `--direction` with `--model_name`.
- Custom checkpoint paths require both `--prompt` and `--direction`; use `a2b` for source-domain A to target-domain B and `b2a` for the reverse direction.
- The source inference script requires CUDA execution and enables xformers memory-efficient attention; the bundled helper only validates and prints commands, it does not run the model.
- The output file uses the input image basename inside `--output_dir`; choose a unique output directory or basename when comparing multiple runs.
