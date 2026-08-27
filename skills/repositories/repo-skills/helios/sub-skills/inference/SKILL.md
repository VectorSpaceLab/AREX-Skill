---
name: inference
description: "Route Helios video generation, demo, and runtime inference workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Inference

Use this sub-skill when the user wants to generate a video with Helios.

## Typical triggers

- "generate a video"
- "run text-to-video"
- "turn this image into a video"
- "animate this clip"
- "use the distilled checkpoint"
- "try the low-VRAM or multi-GPU path"
- "launch the demo"

## What this sub-skill covers

- Text-to-video, image-to-video, and video-to-video generation.
- Base, Mid, and Distilled checkpoint selection.
- Prompt-only and prompt-plus-image/video generation.
- Multi-GPU context parallelism.
- Low-VRAM offload and common runtime toggles.
- The demo-style workflow, with the caveat that the local UI module is not a
  lazy import and can do expensive work at startup.

## What it does not own

- Dataset metadata preparation belongs in `data-preparation`.
- Stage configuration, training launches, and checkpoint merging belong in
  `training`.
- Benchmark/evaluation metrics are not a primary route in this generated skill.

## Read next

- `references/workflows.md` for end-to-end generation choices and run flow.
- `references/cli-reference.md` for the bundled inference helper and the key
  runtime flags it exposes.
- `references/troubleshooting.md` for GPU/backend, import, and input-shape
  failures.
- `scripts/run_helios_inference.py` for the bundled inference helper.

## Working rule

Prefer the bundled helper and the compatibility check before relying on a raw
source checkout or guessing at the backend.
