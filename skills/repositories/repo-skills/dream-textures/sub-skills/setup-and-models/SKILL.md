---
name: setup-and-models
description: "Install and diagnose Dream Textures add-on dependencies, model
  acquisition, tokens, backend variants, and checkpoint configuration choices."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Dream Textures Setup and Models

Use this sub-skill when a user needs help installing or diagnosing the Dream Textures Blender add-on, choosing a dependency/backend variant, completing add-on setup, downloading or linking models, supplying Hugging Face or DreamStudio credentials, or resolving checkpoint/model-type mismatches.

## Route here for

- Installing Dream Textures as an official release or as a source/developer add-on.
- Blender add-on folder naming, add-on registration, missing `.python_dependencies`, or dependency-variant selection for CUDA, ROCm, Apple Silicon/MPS/CPU, DirectML, or DreamStudio cloud use.
- Hugging Face Hub model search/download, private or gated model access tokens, cache visibility, fp16/resume-download choices, or missing model weights.
- DreamStudio API key setup for cloud processing.
- Importing, linking, unlinking, or converting `.ckpt`, `.safetensors`, or `.pth` checkpoints and choosing the correct checkpoint model config.
- Diagnosing model type versus task mismatches such as using a prompt-to-image model for inpaint/outpaint or depth projection.

## Route elsewhere

- Prompt settings, image-to-image, inpaint/outpaint parameter workflows, seamless generation, history, and upscaling usage belong in `../generation-workflows/`.
- 3D texture projection, render pass, render engine, compositor, scene depth/color inputs, and annotation workflows belong in `../scene-integration/`.
- Backend class implementation, public API signatures, generator subprocess internals, scheduler implementation, and custom backend development belong in `../backend-and-api/`.

## Operating procedure

1. Identify whether the user installed an official release archive or a source/developer checkout. Prefer the official prebuilt release for ordinary users; use source/developer dependency steps only for contributors or when a prebuilt variant is not usable.
2. Confirm Blender sees the add-on as a package folder named `dream_textures`, then check the add-on preferences for dependency status, model status, Hugging Face token, linked/imported checkpoints, and DreamStudio key.
3. Select the smallest matching dependency variant for the user's platform/backend rather than installing all variants. Local Diffusers generation needs the packages under the add-on's `.python_dependencies`; DreamStudio cloud use needs an API key and may not require local model weights.
4. For model setup, choose a model type that matches the intended task before debugging prompts: prompt/image-to-image, inpaint/outpaint, depth-to-image/projection, upscaling, SDXL base/refiner, or ControlNet.
5. For checkpoint import or linking, verify the extension and model config. If the config is uncertain, prefer auto-detect only as a first pass and be ready to retry with the explicit v1/v2/depth/inpainting/XL/ControlNet config that matches the checkpoint family.
6. Use the bundled diagnostic script before advising reinstall: `scripts/check_addon_layout.py` safely inspects a user-supplied add-on directory without importing Blender modules, installing packages, downloading models, or using the network.

## Bundled references and tools

- `references/install-and-models.md` explains release-vs-source setup, Blender folder naming, dependency target behavior, add-on preference setup flow, Hugging Face tokens, DreamStudio keys, and model download/link/import operations.
- `references/backend-compatibility.md` summarizes dependency variants, backend selection, package differences, and the task/model-type/checkpoint-config matrix.
- `references/troubleshooting.md` gives concrete validation and recovery steps for install/import, dependency, cache, token, DreamStudio, checkpoint, and model-mismatch failures.
- `scripts/check_addon_layout.py` performs a no-network static layout check of a Dream Textures add-on folder, requirement variants, `.python_dependencies` state, and package-naming hints.
