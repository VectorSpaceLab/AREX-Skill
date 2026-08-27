---
name: conversion-and-maintenance
description: "Use Diffusers CLI helpers, checkpoint and format conversion
  scripts, ONNX export guidance, and repository maintenance checks for copied
  code, dummy objects, dependencies, style, and safe edits."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Conversion And Maintenance

Use this sub-skill when the task is about converting weights or maintaining the Diffusers repository rather than running inference, training, or adapter composition.

## Route Here For

- `diffusers-cli env`, `fp16_safetensors`, and `custom_blocks` command discovery, environment reports, Hub PR conversion helper behavior, or modular custom block packaging.
- Stable Diffusion original checkpoint to Diffusers conversion, Diffusers model to original SD/SDXL single-file conversion, LoRA safetensors merge/extraction scripts, and ONNX export scripts.
- Single-file and local/offline conversion planning, including `from_single_file`, `config`, `local_files_only`, `.safetensors` versus `.ckpt`, and avoiding accidental Hub pushes.
- Repo maintainer work involving copied-code propagation, generated dummy files, optional dependency registration, import guards, `make style`, and focused tests.

## Route Elsewhere

- End-to-end generation, pipeline loading for inference, device placement during generation, or serving: use `../pipelines-and-inference/SKILL.md`.
- Adapter API usage such as `load_lora_weights`, `set_adapters`, `fuse_lora`, textual inversion, IP-Adapter, T2I-Adapter, or ControlNet loading: use `../adapters-and-loaders/SKILL.md`.
- Training or fine-tuning recipes: use `../training-recipes/SKILL.md`.
- Scheduler algorithm changes without conversion/maintenance context: use `../schedulers/SKILL.md`.

## Fast Workflow

1. Classify the request as CLI probe, conversion command planning, ONNX export, single-file/local format handling, or repository maintenance.
2. For CLI/environment questions, run `python scripts/diffusers_cli_probe.py --help` and then a safe probe such as `python scripts/diffusers_cli_probe.py env`.
3. For conversion tasks, run `python scripts/conversion_command_builder.py --help` and emit a command skeleton for the right family before touching weights.
4. Use [references/conversion-workflows.md](references/conversion-workflows.md) to choose required flags, safety checks, and no-push/offline behavior.
5. Use [references/cli-and-maintenance.md](references/cli-and-maintenance.md) for `diffusers-cli`, copied-code, dummy-object, optional dependency, style, and focused test rules.
6. If failures mention missing optional dependencies, CPU/GPU/dtype mismatch, missing local configs, unsafe file formats, bad LoRA prefixes, or copy drift, use [references/troubleshooting.md](references/troubleshooting.md).

## Key Rules

- Prefer local output directories and explicit paths; do not push to the Hub unless the user explicitly asks for it.
- Prefer `.safetensors` for untrusted weights; `.ckpt` uses pickle-style loading and can be unsafe.
- For local/offline single-file work, provide a local `config` directory and `local_files_only=True` rather than relying on Hub inference.
- Choose device and dtype together: CPU for inspection/skeletons, CUDA for fp16-heavy conversion/export, and avoid fp16 ONNX export without CUDA.
- Do not edit `# Copied from ...` blocks directly unless intentionally breaking the copy link; normally edit the source and run `make fix-copies`.

## References

- Conversion workflows: `references/conversion-workflows.md`
- CLI and maintenance: `references/cli-and-maintenance.md`
- Troubleshooting: `references/troubleshooting.md`
- CLI probe: `scripts/diffusers_cli_probe.py`
- Conversion command builder: `scripts/conversion_command_builder.py`
