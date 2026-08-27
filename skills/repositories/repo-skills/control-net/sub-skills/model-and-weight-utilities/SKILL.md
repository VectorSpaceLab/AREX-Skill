---
name: model-and-weight-utilities
description: "Inspect ControlNet model/config APIs and safely reason about
  checkpoint initialization, transfer, and state-dict mappings."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Model and Weight Utilities

Use this sub-skill when a user needs to understand ControlNet architecture/configs, inspect model-loading APIs, dry-run checkpoint key mappings, initialize ControlNet weights from Stable Diffusion, transfer an existing ControlNet to a compatible community checkpoint, or debug checkpoint-loading failures.

For generated-image app usage, route to [gradio-inference-apps](../gradio-inference-apps/SKILL.md). For fine-tuning loops, Fill50K data, `sd_locked`, and dataset schema, route to [training-and-datasets](../training-and-datasets/SKILL.md). For detector outputs and control-map creation, route to [annotators-and-preprocessing](../annotators-and-preprocessing/SKILL.md).

## Quick Routing

- Read [API reference](references/api-reference.md) when inspecting `create_model`, `load_state_dict`, `get_state_dict`, `ControlNet`, `ControlledUnetModel`, `ControlLDM`, or `DDIMSampler` signatures and method responsibilities.
- Read [configuration and architecture](references/configuration-and-architecture.md) when comparing `cldm_v15.yaml` with `cldm_v21.yaml`, explaining `jpg`/`txt`/`hint`, zero convolutions, locked/trainable branches, low-VRAM behavior, or attention options.
- Read [weight utilities](references/weight-utilities.md) when adapting `tool_add_control.py`, `tool_add_control_sd21.py`, or the ControlNet transfer-offset algorithm without destructive hard-coded outputs.
- Read [troubleshooting](references/troubleshooting.md) when checkpoint paths, config/checkpoint pairing, safetensors loading, CUDA/xformers, state-dict prefixes, or overwrite guards fail.
- Run [`scripts/inspect_weight_mapping.py`](scripts/inspect_weight_mapping.py) when a user asks for a non-destructive report of ControlNet key mapping or newly initialized keys before writing a checkpoint.

## Safe Default Workflow

1. Identify the base family first: SD1.x uses `cldm_v15`/SD1.5 initialization; SD2.1 uses `cldm_v21`/SD2.1 initialization.
2. Dry-run key mapping before saving anything: use the bundled inspector with a real checkpoint or `--self-test` for the mapping logic.
3. Treat model creation and checkpoint loading separately: configs define target classes and tensor shapes; checkpoints supply state-dict keys and tensor values.
4. Preserve output safety: the original conversion scripts refuse missing input files, refuse existing output files, and require the output directory to exist; keep those guards in any adapted writer.
5. Avoid network and generation side effects in diagnostics: the bundled inspector performs no downloads, model generation, training, or checkpoint writes.

## Common User Requests

- "Create a ControlNet init checkpoint from SD1.5": read [weight utilities](references/weight-utilities.md), verify the input is an SD1.x checkpoint, dry-run with the inspector, then adapt the documented add-control writer only if an output save is explicitly requested.
- "Explain `cldm_v15` vs `cldm_v21`": read [configuration and architecture](references/configuration-and-architecture.md), especially context dimension, text encoder, attention head settings, and `use_linear_in_transformer`.
- "Dry-run state-dict key mapping": run [`scripts/inspect_weight_mapping.py`](scripts/inspect_weight_mapping.py) with `--config-family sd15` or `sd21` and optionally `--checkpoint`.
- "Debug safetensors loading": read [API reference](references/api-reference.md) for `load_state_dict` behavior and [troubleshooting](references/troubleshooting.md) for dependency/device issues.
- "Explain zero convolution learning": read [configuration and architecture](references/configuration-and-architecture.md) for the distilled FAQ explanation and how zero outputs become trainable after gradient updates.
