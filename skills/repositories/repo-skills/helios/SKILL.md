---
name: helios
description: "Route Helios video-generation, data-preparation, and training workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Helios

Use this repo skill for the Helios family of video-generation workflows built
around Diffusers-style pipelines and the `Helios-Base`, `Helios-Mid`, and
`Helios-Distilled` checkpoints.

## Start here

Before choosing a route, read:

- `references/overview.md` for the supported workflow map and model-family
  summary.
- `references/compatibility.md` for the required Python/package/backend shape.
- `references/api-reference.md` for the verified diffusers/local Helios API
  surfaces used by the bundled workflows.
- `references/troubleshooting.md` for cross-cutting install, import, and GPU
  issues.
- `scripts/check_helios_env.py` for a quick local smoke check of the installed
  environment.

## Routes

### 1) Video generation and demos

Use `sub-skills/inference/SKILL.md` when the user wants to:

- generate text-to-video, image-to-video, or video-to-video clips;
- choose between Base, Mid, or Distilled checkpoints;
- run the public-style Gradio demo flow or local inference;
- use low-VRAM offload, multi-GPU context parallelism, or prompt/video input
  variants.

### 2) Data preparation

Use `sub-skills/data-preparation/SKILL.md` when the user wants to:

- validate Helios dataset metadata or prompt/video layout;
- prepare the metadata, latent, or prompt-embedding inputs that training
  consumes;
- understand the expected JSON/CSV/file naming conventions before launching
  distributed preprocessing jobs.

### 3) Training and fine-tuning

Use `sub-skills/training/SKILL.md` when the user wants to:

- configure or debug Stage 1, Stage 2, or Stage 3 training;
- choose between DDP and DeepSpeed launch patterns;
- validate YAML config constraints before a launch;
- merge or load checkpoints and LoRA-style weights after training.

## What is intentionally out of scope

- The repo's metric-benchmark suite is not a primary runtime route in this
  generated skill. Treat it as a separate maintenance/evaluation concern unless
  a later skill refresh explicitly adds it.
- One-off maintainer scripts, benchmark scratch files, and generated outputs are
  not part of the runtime graph.

## Choosing the right sub-skill

- If the task is "make a video" or "run the demo", start with
  `inference`.
- If the task is "prepare my data" or "check the metadata format", start with
  `data-preparation`.
- If the task is "train", "fine-tune", "resume", or "merge a checkpoint",
  start with `training`.

If a request spans more than one route, handle the earliest blocking step first:
validate inputs, then prepare data, then train, then generate.

## Quick rules

- Prefer the bundled compatibility check before assuming the environment is
  ready.
- Treat CUDA as the core backend for the generation and training routes.
- Treat optional extras such as DeepSpeed, NPU-specific kernels, or demo-only
  UI packages as add-ons, not the baseline.
- Keep all runtime guidance inside the bundled skill tree; do not depend on the
  original repository checkout.
