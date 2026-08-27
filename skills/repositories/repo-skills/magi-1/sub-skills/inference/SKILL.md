---
name: inference
description: "Operate MAGI-1 source-code inference for text-to-video,
  image-to-video, and video-to-video generation."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# MAGI-1 inference

Use this sub-skill when a task needs MAGI-1 source-code inference for text-to-video (`t2v`), image-to-video (`i2v`), or video-to-video / continuation (`v2v`) and the agent must choose configs, edit inference JSON safely, build commands, or troubleshoot CUDA/distributed/checkpoint failures.

Do **not** use this sub-skill for ComfyUI node installation or graph editing; route those tasks to the ComfyUI sub-skill. Prompt enhancement with Dify is only a root-level auxiliary topic and is not covered here beyond prompt text passed into inference.

## Start here

1. Read [references/cli-and-api.md](references/cli-and-api.md) to choose the CLI or `MagiPipeline` API route and assemble `t2v`, `i2v`, or `v2v` arguments.
2. Read [references/configuration.md](references/configuration.md) before editing any MAGI JSON config or switching between 4.5B, 24B, base, distill, and fp8-quant variants.
3. Use [scripts/magi_config_check.py](scripts/magi_config_check.py) to validate config shape, required fields, CFG rules, process-count expectations, and optional checkpoint path existence without loading models.
4. Use [scripts/magi_command_builder.py](scripts/magi_command_builder.py) to print a safe source-code command and recommended environment variables without executing inference.
5. If inference fails or hangs, read [references/troubleshooting.md](references/troubleshooting.md) before changing kernels, checkpoints, distributed settings, or media inputs.

## Hard constraints

- Meaningful MAGI inference is CUDA-backed. Use a runtime stack compatible with the repository requirements, including CUDA-enabled PyTorch plus MAGI's attention/media dependencies, then run the bundled preflight checks in the user's environment. Dependency import success proves only preflight readiness, not checkpoint-backed generation.
- Full generation is **not** a smoke test unless valid MAGI DiT, T5, VAE, and special-token assets are available at the paths referenced by the config and environment.
- `engine_config.pp_size * engine_config.cp_size` must equal the launched distributed world size. Single-process commands require config values of `1 * 1`; multi-GPU configs should use `torchrun`.
- Keep source-code commands rooted at a MAGI source checkout or installed package tree with `inference/` importable. This skill provides operating guidance and bundled helpers; it does not include model weights.

## Evidence distilled

This sub-skill distills the inference CLI, API, config schema, example configs, example launch scripts, video/prompt processing, checkpoint loading, and distributed initialization from the MAGI repository evidence paths named in the references. Source paths are recorded as provenance only; all runtime links in this sub-skill point to generated skill files.
