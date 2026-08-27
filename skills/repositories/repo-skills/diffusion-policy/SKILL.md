---
name: diffusion-policy
description: "Use Diffusion Policy for robot imitation-learning configs, zarr
  replay data, policy/model interfaces, training/evaluation workflows, and
  safety-gated real robot operations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Diffusion Policy

Use this repo skill when a task involves the `diffusion_policy` robotics imitation-learning codebase: Hydra experiment configs, Push-T/Robomimic/Kitchen/BlockPush tasks, zarr demonstration replay buffers, diffusion action policies, checkpoint evaluation, Ray multiruns, or real Push-T robot data collection/evaluation.

## Start with these checks

1. Read [repo provenance](references/repo-provenance.md) before assuming the skill matches a checkout or package version.
2. Read [overview and installation](references/overview-and-installation.md) for dependency variants, package/import behavior, and safe smoke checks.
3. Run the bundled smoke checker when you need environment evidence without training, downloads, Ray, cameras, or robot motion:

   ```bash
   python scripts/smoke_check.py --json
   ```

4. Use [cross-cutting troubleshooting](references/troubleshooting.md) for import, Hydra, dependency, dataset, CUDA, simulator, W&B, and hardware failures.

## Route by task

| If the user needs... | Read |
|---|---|
| Build or debug single-seed training, checkpoint evaluation, Hydra overrides, Ray multiruns, output trees, W&B/logs, or benchmark command structure | [training-and-evaluation](sub-skills/training-and-evaluation/SKILL.md) |
| Inspect or validate zarr/zip ReplayBuffer stores, dataset sample schemas, `SequenceSampler`, normalizers, or dataset conversion assumptions | [data-and-replay-buffers](sub-skills/data-and-replay-buffers/SKILL.md) |
| Choose/inspect low-dim, image, hybrid, diffusion UNet/Transformer, Robomimic, BET, or IBC policy/model families; debug shape, normalizer, checkpoint, or device issues | [policies-and-models](sub-skills/policies-and-models/SKILL.md) |
| Preflight UR5 + RealSense + SpaceMouse workflows, demo capture, real robot policy evaluation, shared-memory IO, real dataset conversion, or hardware safety gates | [real-robot-operations](sub-skills/real-robot-operations/SKILL.md) |

## What this skill covers

- The core `Dataset` -> `Normalizer` -> `Policy` -> `EnvRunner` -> `Workspace` workflow.
- Low-dimensional and image observation/action interfaces, including horizon terminology (`horizon`, `n_obs_steps`, `n_action_steps`).
- Hydra workspace/task config composition and command-building patterns.
- ReplayBuffer zarr/zip store structure and episode validation.
- Checkpoint evaluation behavior, including EMA model selection.
- Optional simulator, CUDA, Ray, W&B, Robomimic, MuJoCo, and real-robot dependency boundaries.
- Safety-gated real-robot operations: UR RTDE, RealSense, SpaceMouse, shared-memory queues/ring buffers, timestamp alignment, and conversion of recorded episodes.

## Boundaries and safety

- Do not launch training, Ray workers, data downloads, W&B online logging, simulator rollouts, camera capture, or robot motion as a smoke check.
- Do not treat a CPU import check as proof that benchmark-scale CUDA, MuJoCo/Robomimic, or real-robot workflows are ready.
- Stop for explicit operator confirmation before any live robot action, camera recording, or command that may overwrite run outputs.
- When a workflow needs project entrypoints or config files, first verify that the user is operating in a compatible Diffusion Policy checkout or equivalent project layout; this skill provides reusable operating knowledge and safe helpers, not the full benchmark runtime.

## Bundled scripts

- [scripts/smoke_check.py](scripts/smoke_check.py) checks distribution metadata, representative imports, optional config root counts, and optional torch CUDA visibility without side effects.
- Sub-skill helpers validate config composition, summarize multirun logs, inspect ReplayBuffer stores, inspect policy interfaces, and preflight real-robot dependencies.

## Refresh and verification notes

This skill was generated from a clean source snapshot before skill-output files were added. If a checkout has a different commit, changed config targets, dependency files, entrypoint options, dataset/policy/workspace classes, or real-robot APIs, refresh the repo skill before relying on detailed commands or signatures.
