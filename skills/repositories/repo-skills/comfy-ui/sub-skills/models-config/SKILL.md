---
name: models-config
description: "Configure ComfyUI model folders, extra model paths, supported
  model families, backend/memory flags, quantization choices, and model-loading
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# ComfyUI Models and Configuration

Use this sub-skill when the user needs to place or find models, create or validate `extra_model_paths.yaml`, diagnose missing checkpoints/LoRAs/VAEs/ControlNets, choose memory/backend flags, or understand which model families ComfyUI can load.

## Quick Routing

- Model folders and `extra_model_paths.yaml`: read `references/model-paths.md` and run `scripts/validate_extra_model_paths.py` before suggesting a launch.
- Backend or memory flags such as `--cpu`, `--lowvram`, `--highvram`, `--directml`, `--reserve-vram`, or `--disable-dynamic-vram`: read `references/backend-and-memory.md`; for launch/server details cross-link to `../server-api/SKILL.md`.
- Supported model families, split checkpoint vs standalone diffusion/text/VAE model layout, and quantized checkpoints: read `references/model-families.md`.
- Missing model, wrong folder category, optional dependency/import failure, YAML syntax, VRAM pressure, or quantization compatibility: read `references/troubleshooting.md`.
- Workflow graph references to loader nodes or prompt JSON fields belong in `../workflow-execution/SKILL.md`; this sub-skill only explains how those referenced model names are resolved.

## Default Model Categories

ComfyUI resolves model filenames by category. The most common categories are:

- `checkpoints`: all-in-one `.ckpt`, `.safetensors`, `.pt`, `.pth`, `.bin`, `.pkl`, `.sft`, and related checkpoint files.
- `configs`: YAML model configs.
- `loras`, `vae`, `controlnet`, `upscale_models`, `embeddings`, `hypernetworks`: specialized add-on model folders.
- `text_encoders`: standalone CLIP/T5/text encoder files; legacy `clip` maps here.
- `diffusion_models`: standalone diffusion/UNet files; legacy `unet` maps here.
- `clip_vision`, `style_models`, `diffusers`, `vae_approx`, `gligen`, `model_patches`, and media/model helper categories such as `audio_encoders`, `classifiers`, `detection`, `background_removal`, `frame_interpolation`, `geometry_estimation`, and `optical_flow`.
- `custom_nodes`: extension folders; route implementation questions to `../custom-nodes/SKILL.md`.

## Extra Model Paths Pattern

`extra_model_paths.yaml` has top-level profile names. Each profile may define `base_path`, optional `is_default`, and one or more model categories. Category values are strings; use YAML block strings for multiple folders.

```yaml
shared-models:
  base_path: /mnt/models
  is_default: true
  checkpoints: checkpoints
  loras: |
    loras
    community/loras
  vae: vae
  controlnet: |
    controlnet
    t2i_adapter
```

Rules to preserve when editing:

- If `base_path` is present, category entries are resolved relative to it unless already absolute.
- Without `base_path`, relative category entries resolve relative to the YAML file location.
- `is_default: true` moves those paths ahead of existing category paths; it does not download or create models.
- Re-adding the same path to a category is ignored unless `is_default` moves it to the front.
- `clip` and `unet` are legacy names; prefer `text_encoders` and `diffusion_models` in new configs.

## Bundled Validator

Use the bundled validator before telling an agent to launch with an extra config:

```bash
python scripts/validate_extra_model_paths.py extra_model_paths.yaml --strict
```

Useful modes:

- `--strict`: fail on unknown categories and missing directories.
- `--allow-missing`: report missing directories as warnings instead of errors.
- `--json`: print machine-readable resolved paths and diagnostics.

The validator mirrors ComfyUI's safe path-resolution shape without importing ComfyUI, torch, or model-loading modules.

## Backend and Memory Defaults

- Do not assume CUDA. ComfyUI supports NVIDIA/CUDA, AMD/ROCm, Intel/XPU, Apple MPS, CPU, DirectML, and other torch-backed devices when the matching PyTorch/backend packages are installed.
- `--cpu` runs everything on CPU and is slow, but useful for diagnosis or GPU-less machines.
- Dynamic VRAM is normally enabled unless disabled by incompatible modes or explicit flags. Prefer `--vram-headroom` or `--reserve-vram` before disabling it.
- `--highvram` keeps models in GPU memory; `--lowvram` and `--novram` are for constrained memory, with `--novram` more aggressive.
- Precision flags such as `--fp16-unet`, `--bf16-unet`, `--fp8_e4m3fn-unet`, `--fp16-vae`, and text-encoder fp8/fp16/fp32 flags must match backend capability and model tolerance.

## Safe Response Checklist

When answering model/config requests:

1. Identify whether the problem is path resolution, model family/layout, backend capability, memory pressure, or graph loader-node naming.
2. Validate YAML syntax and resolved paths with the bundled script when an `extra_model_paths.yaml` is involved.
3. Name the exact category the model loader expects, especially for `checkpoints`, `loras`, `vae`, `controlnet`, `text_encoders`, and `diffusion_models`.
4. Avoid promising downloads; ComfyUI core does not download local models unless the user chooses features that fetch external assets.
5. Mention optional dependency/backend caveats generically: missing torch backend packages, optional acceleration packages, or API-node dependencies can fail independently of model paths.
