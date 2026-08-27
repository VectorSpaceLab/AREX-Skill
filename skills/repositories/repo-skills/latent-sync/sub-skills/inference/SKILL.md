---
name: inference
description: "Run LatentSync single-pair, small-batch, Gradio, and
  deployment-aware inference workflows safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Inference

Use this sub-skill when you need LatentSync to synthesize lip-synced video from an input video and an input audio file, or when you need to launch the local demo UI.

Do not use this sub-skill for training, raw preprocessing pipeline stages, or SyncNet/FVD scoring.

## What this sub-skill owns

- Single-pair generation through the repo-maintained `scripts.inference` module.
- A safer replacement for the demo shell command with explicit repository root, config, checkpoint, input, output, temp, seed, and DeepCache controls.
- Small-batch generation for file-list or pair-list inputs when outputs are only being produced.
- Gradio demo launch with explicit `share` and browser behavior instead of implicit public sharing.
- Reference-only notes for Cog/Replicate deployment entry points.

## Route here when the request is about

- Running the demo assets or a user-supplied video/audio pair.
- Choosing between the 256 and 512 U-Net inference configs.
- Enabling or disabling DeepCache during generation.
- Launching, smoke-checking, or adapting the Gradio app.
- Understanding Cog/Replicate inference behavior before adapting it elsewhere.

## Do not route here when the request is about

- Selecting training stages, launching U-Net/SyncNet training, or editing train configs. Use the training sub-skill when available.
- Processing raw datasets into face-aligned training clips. Use the data-preparation sub-skill.
- Scoring generated outputs with SyncNet confidence, SyncNet accuracy, or FVD. Use `../evaluation/SKILL.md` when outputs are being evaluated.
- Downloading remote weights or running network-only deployment helpers as local inference.

## Start here

1. Read `references/workflows.md` for single-pair, batch, and UI launch flows.
2. Read `references/api-reference.md` for prompt-safe CLI, function, pipeline, and config notes.
3. Read `references/troubleshooting.md` before long GPU runs or when a preflight check fails.
4. Use `scripts/run_inference.py` for CLI and small-batch generation.
5. Use `scripts/launch_gradio.py` for local UI launch or Gradio import smoke tests.
6. Read `references/deployment.md` only when adapting Cog/Replicate behavior.

## Runtime rules

- Always pass `--repo-root` to helper scripts so imports, configs, checkpoints, masks, and assets resolve from the intended LatentSync runtime tree.
- Prefer `configs/unet/stage2_512.yaml` for the released v1.6 checkpoint and `configs/unet/stage2.yaml` for a v1.5 or 256-resolution checkpoint.
- Treat missing `checkpoints/latentsync_unet.pt`, missing Whisper weights, missing `ffmpeg`, and unavailable CUDA as preflight blockers.
- Keep temp directories isolated; the underlying pipeline deletes and recreates its `temp_dir`.
- Use the evaluation sub-skill only after batch outputs need scores.
