---
name: inference
description: "Routes DreamOmni2 command-line image editing and generation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# DreamOmni2 inference

Use this sub-skill when the user wants to run the DreamOmni2 CLI workflows that take two images plus an instruction and produce either an edited image or a newly generated image.

## Typical triggers
- "generate an image with DreamOmni2"
- "edit this image with DreamOmni2"
- "run the generation CLI"
- "run the editing CLI"
- "what do the two input images mean in the DreamOmni2 scripts?"

## What belongs here
- The two-image editing workflow
- The two-image generation workflow
- The VLM prompt stage that turns the instruction into a diffusion prompt
- The diffusion pipeline invocation and saved output path
- CLI validation and prompt/input-order troubleshooting for these workflows

## What does not belong here
- Gradio launchers and browser-facing UI issues; use `sub-skills/web-demo/`
- Training, checkpointing, or distributed optimization helpers
- Generic Diffusers or generic VLM tasks that are not DreamOmni2-specific

## Read these files first
- `references/workflows.md` for the edit vs generation command shapes and input order
- `references/api-reference.md` for the verified pipeline and helper signatures
- `references/troubleshooting.md` for GPU, model-path, prompt, and output failures
- `../../scripts/dreamomni2_common.py` for the shared prompt/image helpers used by both wrappers

## Bundled scripts
- `scripts/inference_edit.py` for the editing CLI
- `scripts/inference_gen.py` for the generation CLI

## Workflow outline
1. Confirm whether the task is editing or generation.
2. Confirm the two input images and the instruction text.
3. Confirm the model paths, especially the VLM checkpoint and the matching LoRA directory.
4. For editing, make sure the source image is first and the reference image is second.
5. Run the bundled CLI wrapper and save the output image.
6. If the result is wrong, inspect the prompt stage and the image order before changing the model stack.

## Decision points
- **Editing vs generation**: the same VLM prompt stage is used, but editing and generation load different LoRA adapters and have different output expectations.
- **Default size**: generation exposes height and width; editing uses the resized source image dimensions.
- **Prompt text**: the wrapped VLM stage should preserve the task-specific prefix so the downstream diffusion prompt is well formed.

## If you need more detail
Read the linked reference files when you need exact parameter names, supported image types, or a recovery path for a missing model or GPU.
