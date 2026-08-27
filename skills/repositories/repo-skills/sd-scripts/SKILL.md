---
name: sd-scripts
description: "Use sd-scripts for Stable Diffusion and image-model training,
  dataset preparation, image generation, LoRA/model utilities, and
  troubleshooting across SD1/2, SDXL, SD3, FLUX, Lumina, HunyuanImage, and Anima
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# sd-scripts

Use this skill when a user asks for help with `sd-scripts`, Kohya-style Stable Diffusion training scripts, LoRA/additional-network training, dataset TOML preparation, image generation, or model/LoRA utility workflows.

This skill is self-contained for planning, validation, troubleshooting, and command construction. Heavyweight sd-scripts training/generation/merge commands still require the user to run them in an sd-scripts installation that contains the project scripts, model files, and required ML dependencies.

## Route by Task

- Use `sub-skills/data-preparation` for dataset TOML, DreamBooth/fine-tuning subsets, metadata JSON/JSONL, captions/tags, validation splits, bucketing, masked loss, inpainting data, and safe input validation.
- Use `sub-skills/training` for LoRA/additional-network training, full fine-tuning, Textual Inversion, LECO, ControlNet-LLLite, validation loss, memory flags, optimizer choices, and model-family training commands.
- Use `sub-skills/generation` for image generation, txt2img/img2img/inpainting inference, prompt-file validation, SDXL conditioning, LoRA application during inference, ControlNet/LLLite generation, and minimal inference scripts.
- Use `sub-skills/model-utilities` for LoRA merge/extract/resize/convert planning, checkpoint or Diffusers conversion, safetensors metadata inspection, model-spec metadata, and safe handling of write-heavy utilities.

## Before Suggesting a Runnable Command

1. Confirm the user has an sd-scripts checkout or installed copy with the relevant root scripts available.
2. Confirm Python dependencies are installed for the chosen workflow. Training and generation usually need PyTorch, Accelerate, Diffusers, Transformers, Safetensors, and model-family-specific optional packages.
3. Confirm model files, text encoders, VAE/AE files, datasets, and output directories exist.
4. Confirm whether execution is safe: full training, generation, caching, merging, extraction, and conversion can use GPU, download/load large weights, write large files, or run for a long time.
5. Use bundled helper scripts for read-only validation or command construction before running heavyweight sd-scripts commands.

## Installation and Environment Notes

sd-scripts is normally used from a cloned checkout with Python 3.10-3.12 and a workflow-specific PyTorch install. PyTorch is intentionally not pinned in the project requirements because CUDA, driver, GPU architecture, and platform determine the correct wheel.

A typical setup pattern is:

```bash
python -m venv venv
source venv/bin/activate
python -m pip install torch torchvision --index-url <matching-pytorch-wheel-index>
python -m pip install --upgrade -r requirements.txt
accelerate config
```

On Windows, use the venv activation command for PowerShell or cmd, and match the PyTorch CUDA wheel to the installed NVIDIA driver. For RTX 50-series or other new GPUs, use a recent PyTorch/CUDA wheel that supports the architecture.

## Safe Bundled Helpers

- `scripts/check_sd_scripts_environment.py` checks the active Python for common dependencies and optional backend availability without importing or running training scripts.
- `sub-skills/data-preparation/scripts/validate_dataset_inputs.py` validates dataset config and metadata files without loading models.
- `sub-skills/training/scripts/build_training_command.py` prints command templates and never launches training.
- `sub-skills/generation/scripts/validate_prompt_file.py` validates prompt files without loading models.
- `sub-skills/model-utilities/scripts/inspect_safetensors_metadata.py` reads safetensors metadata without loading tensor payloads.

## Shared References

- `references/repo-provenance.md`: source snapshot used to generate this skill; read before deciding whether to refresh the skill.
- `references/troubleshooting.md`: cross-cutting install, dependency, hardware, and execution-safety failures.
- `references/developer-notes.md`: repo-specific conventions for coding agents and maintainers.

## Safety Defaults

- Do not run training, generation, caching, merging, extraction, or conversion just because a command can be built.
- Prefer read-only validators, `--help`, metadata inspection, and dry-run planning first.
- Do not use the same file as both input and output for model utilities.
- Treat network downloads, model downloads, external credentials, and long GPU jobs as explicit user-approved operations.
- When dependencies are missing, explain the minimal dependency group for the requested workflow instead of installing every optional package.
