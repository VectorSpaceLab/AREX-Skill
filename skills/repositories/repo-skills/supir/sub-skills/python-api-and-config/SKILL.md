---
name: python-api-and-config
description: "Use SUPIR's Python APIs, model/config objects, image/tensor
  helpers, and LLaVA caption bridge without running batch scripts or demos."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Python API and Config

Use this sub-skill when the task asks how to import SUPIR modules, construct a
SUPIR model, inspect YAML config behavior, call `batchify_sample`, use the
LLaVA caption bridge, convert images/tensors, validate dtype choices, or debug
API-level import/config errors.

Do not use this sub-skill for folder CLI orchestration or browser UI launch.
Route those to [../batch-restoration/SKILL.md](../batch-restoration/SKILL.md)
and [../interactive-demos/SKILL.md](../interactive-demos/SKILL.md).

## Read these bundled files

- [references/api-and-config.md](references/api-and-config.md) for signatures,
  parameter behavior, config loading, and API gotchas.
- [scripts/supir_api_probe.py](scripts/supir_api_probe.py) for a safe import,
  signature, CUDA, and optional config probe.
- [../../references/checkpoints-and-environment.md](../../references/checkpoints-and-environment.md)
  before running anything that loads checkpoints.
- [../../references/troubleshooting.md](../../references/troubleshooting.md)
  for shared dependency, CUDA, Transformers/LLaVA, and checkpoint failures.

## Quick decision path

1. If the user only needs names/signatures, run the probe with `--signatures`.
   Add `--skip-llava` when captioning is intentionally out of scope.
2. If the user has a YAML config, run the probe with `--config <path>` and the
   root checkpoint validator before `create_SUPIR_model`.
3. If the user wants to generate captions, verify `LLavaAgent` import and
   checkpoint variables first; do not instantiate the agent without the model
   path and CUDA plan.
4. If the user wants restoration output, use this sub-skill to validate API
   parameters, then hand off to batch or demo workflow routes.

## Core APIs

- `SUPIR.util.create_SUPIR_model(config_path, SUPIR_sign=None, load_default_setting=False)` loads YAML, SDXL, optional SUPIR base, and Q/F checkpoints.
- `SUPIRModel.batchify_denoise(x, is_stage1=False)` denoises RGB tensors in `[-1, 1]`.
- `SUPIRModel.batchify_sample(...)` runs the restoration sampler with prompt,
  CFG, control, color-fix, and seed controls.
- `SUPIRModel.init_tile_vae(encoder_tile_size=512, decoder_tile_size=64)` adds tiled VAE hooks.
- `LLavaAgent(model_path, device='cuda', conv_mode='vicuna_v1', load_8bit=False, load_4bit=False)` wraps local LLaVA captioning.
- Image helpers expect RGB inputs and generally round spatial sizes to multiples
  of 64 for model compatibility.

## Boundary reminders

- This sub-skill describes API surfaces and validation; it does not run native
  end-to-end inference by default.
- CPU import checks are useful for signatures but do not validate SUPIR output.
- If multiple samples are requested through `batchify_sample`, the source model
  asserts batch size one.
- Local prompt lists are a special tiled-mode path; route detailed usage to
  [../interactive-demos/SKILL.md](../interactive-demos/SKILL.md).

## Safe examples

```bash
python sub-skills/python-api-and-config/scripts/supir_api_probe.py --signatures --check-cuda
python sub-skills/python-api-and-config/scripts/supir_api_probe.py --signatures --skip-llava
python sub-skills/python-api-and-config/scripts/supir_api_probe.py --config path/to/SUPIR_v0.yaml
```

These commands inspect imports, signatures, and config metadata only. They do
not call `create_SUPIR_model` or load checkpoints.
