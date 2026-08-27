---
name: dreamomni2
description: "Routes DreamOmni2 image generation, image editing, and Gradio demo workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# DreamOmni2

Use this skill when the task names DreamOmni2, FLUX.1-Kontext, two-image instruction-based image editing, two-image image generation, or the bundled Gradio demos.

## What this skill covers
- Two-image editing and generation on a CUDA GPU
- The VLM prompt stage that converts instructions into a diffusion prompt
- Gradio launchers for the editing and generation demos
- Shared model-path, environment, and troubleshooting guidance

## Prerequisites
- NVIDIA CUDA hardware with enough VRAM for the DreamOmni2 / Qwen2.5-VL / FLUX.1-Kontext stack
- Python 3.11 or another supported modern CPython
- Runtime dependencies from `requirements.txt` plus Gradio
- Local model assets or hub IDs for the VLM and LoRA weights

## Start here
1. Read `references/model-setup.md` for the expected model layout.
2. Run `scripts/check_env.py` to verify the Python, torch, and GPU setup.
3. Run `scripts/check_models.py` to confirm the model paths you intend to use.
4. Choose the matching sub-skill:
   - `sub-skills/inference/` for CLI generation and editing.
   - `sub-skills/web-demo/` for the Gradio launchers.

## Shared runtime helpers
- `scripts/dreamomni2_common.py` contains the bundled image-resize and prompt-format helpers used by both sub-skills.
- `references/troubleshooting.md` collects the shared install, GPU, model-path, and import failures.

## Route map
### `sub-skills/inference/`
Use this route for:
- editing one source image with a second reference image
- generating a new image from two references
- prompt-stage and diffusion-pipeline questions
- `inference_edit.py` and `inference_gen.py`-style command-line runs

### `sub-skills/web-demo/`
Use this route for:
- launching the editing or generation Gradio UI
- choosing ports, server names, and upload order
- UI-specific troubleshooting such as port conflicts and browser launch issues

## Do not use this skill for
- training, FSDP, or distributed optimization helpers
- dataset preparation or benchmark infrastructure
- generic diffusion research that is not DreamOmni2-specific

## Routing notes
- The CLI and web demo workflows both depend on the same model layout and the same CUDA-capable stack.
- The editing workflow requires the source image to be first and the reference image to be second.
- The generation workflow uses the same two-image VLM prompt stage but a different LoRA adapter.
- If the user only needs installation or model-layout validation, start with the root helper scripts and the model-setup reference before going into a sub-skill.
