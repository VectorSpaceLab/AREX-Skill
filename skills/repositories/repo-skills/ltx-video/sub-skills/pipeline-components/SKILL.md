---
name: pipeline-components
description: "Guides direct LTX-Video pipeline, scheduler, VAE, transformer,
  conditioning, and component diagnostic workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Pipeline Components

Use this sub-skill when the task is about direct Python use or debugging of LTX-Video components rather than end-user command construction.

## Use when

- The user says: "use `LTXVideoPipeline` directly", "`ConditioningItem`", "scheduler timestep", "`RectifiedFlowScheduler`", "VAE downscale factor", "load safetensors checkpoint", "multi-scale class", "`skip_layer_strategy`", "`tone_map_latents`", or "component smoke".
- The user already has package components or checkpoints and needs API signatures, shapes, validation rules, or safe diagnostics.
- The user needs a no-download component smoke for scheduler/VAE configuration behavior.

## Route away

- For CLI commands, `InferenceConfig`, `infer(...)`, media file loading, output writing, or normal local generation workflows, route to `../local-inference/SKILL.md`.
- For YAML pipeline config choice, model-family selection, FP8-vs-bfloat16 config choice, or multi-scale config fields, route to `../model-configs/SKILL.md`.
- For full checkpoint inference quality, prompt quality, or performance benchmarking, do not use component smokes as proof; use the inference route and an explicitly authorized generation run.

## Read order

1. `references/component-api.md` for direct pipeline, conditioning, prompt enhancement, skip-layer, multi-scale, and shape contracts.
2. `references/scheduler-and-vae.md` for scheduler math, VAE/transformer/latent-upsampler loading, and safe component-check facts.
3. `references/troubleshooting.md` when a direct component call fails.
4. `scripts/check_components.py --help` for no-download diagnostics.

## Operating rules

- Prefer verified signatures and runtime facts over source-code guesses.
- Keep direct pipeline snippets explicit about tensor ranks, latent shapes, dtype/device, and checkpoint-loading assumptions.
- Never claim that `scripts/check_components.py`, scheduler tests, or demo VAE config checks verify full LTX checkpoint generation.
- Avoid downloading checkpoints or loading prompt-enhancer models during component diagnosis unless the user explicitly authorizes that heavier workflow.
