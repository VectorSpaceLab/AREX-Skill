---
name: paired-inference
description: "Route Pix2Pix-Turbo paired image-translation inference for
  edge-to-image, stochastic sketch-to-image, custom Pix2Pix checkpoints, and
  local paired Gradio demos."
disable-model-invocation: true
metadata:
  disco-role: operating
  root-skill: img2img-turbo
license: MIT
---

# Paired Inference Router

Use this sub-skill when the task is Pix2Pix-Turbo paired image translation:

- Canny edge-to-image from an RGB image plus a text prompt.
- Stochastic sketch-to-image from a sketch plus a text prompt, guidance value, and seed.
- Inference from a custom Pix2Pix-Turbo checkpoint produced by the paired training workflow.
- Local Gradio demos for the paired Canny and sketch interfaces.

Do not use this sub-skill for unpaired CycleGAN-Turbo translation; route that to `unpaired-inference`. Do not use it for dataset layout, training, or checkpoint creation; route those to `training`.

## Operating references

1. Read [CLI and API reference](references/cli-and-api.md) for exact selectors, flags, constructor and forward signatures, output files, and checkpoint schema expectations.
2. Use [workflows](references/workflows.md) for ready-to-adapt edge, sketch, custom-checkpoint, and Gradio recipes.
3. Use [troubleshooting](references/troubleshooting.md) for CUDA/download, selector, prompt, resize, Canny/gamma, and Gradio failures.

## Bundled safe helpers

These helpers do not run model inference or launch a server by default:

- [`scripts/build_paired_inference_command.py`](scripts/build_paired_inference_command.py) validates paired inference arguments and prints the source-checkout command.
- [`scripts/preview_canny.py`](scripts/preview_canny.py) writes a local Canny control/preview image without downloading models.
- [`scripts/build_gradio_command.py`](scripts/build_gradio_command.py) prints the paired Gradio launch command and prerequisites.

## Safety and evidence limits

The source paired inference code is CUDA-oriented and constructs Stable Diffusion Turbo components plus Pix2Pix-Turbo LoRA checkpoints before inference. This generated sub-skill preserves the verified command/API behavior and safe parser/preprocessing helpers, but it does not claim that full model inference, checkpoint download, Gradio serving, or training was executed during skill drafting.
