---
name: diffusers
description: "Use this skill for Hugging Face Diffusers tasks: pipeline
  inference, schedulers, adapters/loaders, training recipes, modular pipelines,
  conversion helpers, CLI checks, and repo maintenance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Diffusers

Use this skill when a task involves Hugging Face Diffusers APIs, pipeline wiring, model loading, scheduler configuration, adapters, training command planning, modular pipelines, checkpoint conversion, or maintaining the Diffusers repository.

## Start Here

1. Check whether the user is using Diffusers as a package, editing a Diffusers checkout, or converting/training model assets.
2. Verify install and optional backends with [`scripts/check_diffusers_environment.py`](scripts/check_diffusers_environment.py) when imports, CUDA, CLI availability, or optional dependencies are uncertain.
3. Route to the narrowest sub-skill below instead of reading every reference.
4. Keep model downloads, Hub pushes, training runs, and conversion jobs opt-in; many Diffusers workflows are network-, credential-, GPU-, or memory-sensitive.
5. Read [`references/repo-provenance.md`](references/repo-provenance.md) before deciding whether this skill is stale for a current Diffusers checkout.
6. Use [`references/troubleshooting.md`](references/troubleshooting.md) for cross-cutting install/import/backend failures before diving into workflow-specific troubleshooting.

## Installation Baseline

For normal package use, install Diffusers with the backend needed for the task:

```bash
python -m pip install diffusers torch accelerate transformers safetensors
```

For source-checkout development, install editable package dependencies in an isolated environment:

```bash
python -m pip install -e .
python -m pip install torch accelerate transformers safetensors
```

Add extras only when the selected workflow needs them:

- Training recipes commonly need `accelerate`, `datasets`, `protobuf`, `tensorboard`, `Jinja2`, `peft`, and `timm`.
- Quantization and accelerator paths may need `bitsandbytes`, `gguf`, `optimum-quanto`, `torchao`, `nvidia-modelopt`, xFormers, ONNX Runtime, OpenVINO, or vendor-specific packages.
- Flax/JAX, ONNX, TensorRT, Core ML, and other backend workflows require separate backend-specific installs.

Minimal import check:

```bash
python - <<'PY'
import diffusers
print(diffusers.__version__)
from diffusers import DiffusionPipeline, DDPMScheduler
print(DiffusionPipeline, DDPMScheduler)
PY
```

## Route by Task

- **Pipeline inference and serving**: use [`sub-skills/pipelines-and-inference/SKILL.md`](sub-skills/pipelines-and-inference/SKILL.md) for `DiffusionPipeline.from_pretrained`, `AutoPipeline*`, text-to-image, img2img, inpainting, ControlNet/T2I-Adapter/IP-Adapter execution context, callbacks, batching, seeds, device maps, offload, local/offline loading, and server-safe invocation.
- **Schedulers and sampling**: use [`sub-skills/schedulers/SKILL.md`](sub-skills/schedulers/SKILL.md) for DDIM/DDPM/Euler/DPM-Solver/FlowMatch/LCM schedulers, `set_timesteps`, custom timesteps/sigmas, `prediction_type`, Karras/AYS settings, scheduler config round-trips, and sampler troubleshooting.
- **Adapters and loaders**: use [`sub-skills/adapters-and-loaders/SKILL.md`](sub-skills/adapters-and-loaders/SKILL.md) for LoRA/PEFT, textual inversion, IP-Adapter, T2I-Adapter, ControlNet loading, single-file checkpoints, adapter fusion/unloading, state-dict validation, and local-file loading plans.
- **Training recipes**: use [`sub-skills/training-recipes/SKILL.md`](sub-skills/training-recipes/SKILL.md) for DreamBooth, LoRA, textual inversion, text-to-image, ControlNet, T2I-Adapter, InstructPix2Pix, SDXL, SD3, Flux, dataset layout checks, and `accelerate launch` planning.
- **Modular pipelines**: use [`sub-skills/modular-pipelines/SKILL.md`](sub-skills/modular-pipelines/SKILL.md) for `ModularPipeline`, pipeline blocks, states, component managers, sequential/loop blocks, custom block packaging, and modular-pipeline tests.
- **Conversion, CLI, and maintenance**: use [`sub-skills/conversion-and-maintenance/SKILL.md`](sub-skills/conversion-and-maintenance/SKILL.md) for `diffusers-cli`, environment reports, safe conversion planning, ONNX/export notes, copied-code maintenance, dummy dependency checks, style, and focused repo tests.

## Boundary Rules

- Do not start training, conversion, Hub upload, benchmark, or long inference jobs without explicit user confirmation.
- Do not assume a GPU-specific package is installed just because the host has GPUs; run the environment checker and inspect `torch.cuda.is_available()`.
- Do not rely on original Diffusers repo docs, examples, or scripts when using this skill as a standalone runtime skill. The sub-skills include distilled references and safe helpers.
- When the user is editing a Diffusers checkout, follow the repo's copied-code policy: do not edit `# Copied from ...` blocks directly unless intentionally breaking the copy link; run copy/style checks before PR handoff.
- Keep pipeline execution guidance separate from training and conversion guidance. Loading an adapter for inference belongs to adapters/loaders plus pipelines; training that adapter belongs to training recipes.
- Treat original repo tests and examples as native verification candidates for a checkout, not as runtime dependencies for this skill.

## High-Value Helpers

- [`scripts/check_diffusers_environment.py`](scripts/check_diffusers_environment.py): verifies Diffusers import, distribution metadata, optional packages, torch/CUDA status, and `diffusers-cli` help/env availability.
- [`sub-skills/pipelines-and-inference/scripts/pipeline_invocation_template.py`](sub-skills/pipelines-and-inference/scripts/pipeline_invocation_template.py): prints safe no-download pipeline invocation skeletons.
- [`sub-skills/schedulers/scripts/scheduler_smoke.py`](sub-skills/schedulers/scripts/scheduler_smoke.py): checks common scheduler construction and tiny deterministic behavior.
- [`sub-skills/adapters-and-loaders/scripts/adapter_state_check.py`](sub-skills/adapters-and-loaders/scripts/adapter_state_check.py): validates local adapter/checkpoint paths and optional dependency availability.
- [`sub-skills/training-recipes/scripts/training_command_builder.py`](sub-skills/training-recipes/scripts/training_command_builder.py): builds safe training argument plans for user-provided entrypoints.
- [`sub-skills/modular-pipelines/scripts/modular_block_skeleton.py`](sub-skills/modular-pipelines/scripts/modular_block_skeleton.py): generates a minimal custom block skeleton.
- [`sub-skills/conversion-and-maintenance/scripts/conversion_command_builder.py`](sub-skills/conversion-and-maintenance/scripts/conversion_command_builder.py): builds safe conversion argument plans for user-provided entrypoints.

## Common Decision Points

- **Package use vs repo maintenance**: package use usually routes to pipelines, schedulers, adapters, training, or modular pipelines. Editing source, dependency tables, copied code, or CLI modules routes to conversion/maintenance.
- **Local/offline vs Hub access**: prefer `local_files_only=True`, local config paths, and safetensors for offline or untrusted-file work. Ask before using gated models or private tokens.
- **CPU vs CUDA**: CPU is suitable for import checks and skeleton planning. Real generation/training/conversion may need CUDA, bf16/fp16, offload, or smaller fixtures.
- **Adapters vs full model changes**: LoRA/textual inversion/IP-Adapter/T2I-Adapter loading is usually reversible and belongs to adapters/loaders; merging or extracting weights belongs to conversion/maintenance; training new adapters belongs to training recipes.
- **Classic vs modular pipelines**: use classic pipelines for most user generation tasks; use modular pipelines when the user needs block/state/component customization or custom block packaging.

## Verification Expectations

For generated code or guidance, prefer the smallest safe check first:

- Import and CLI help checks for environment issues.
- Parser/help or dry-run checks for skill-owned helper scripts.
- Tiny local fixtures for dataset or adapter path validation.
- Focused native pytest selections only when working in a Diffusers checkout and the commands are short, deterministic, and safe.
- Skip and document checks that require network, credentials, real model weights, long training, destructive writes, or unavailable hardware.
