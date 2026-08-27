---
name: embodied-workflows
description: "Guides RLinf embodied training, simulator, real-robot,
  reward-data, offline-RL, SFT, model, environment, Hydra configuration, and
  static preflight workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# RLinf embodied workflows

Use this sub-skill when a task asks about RLinf embodied training setup, simulator or real-world robot recipes, VLA/VLM model and environment YAML choices, reward-model data collection, offline-RL/SFT intersections, or static preflight review before an expensive run.

Do **not** launch training, evaluation, robot motion, asset downloads, or hardware probes just because this skill is loaded. First identify the target environment family, model family, algorithm, assets, cluster topology, and whether the user wants planning only or an actual run.

## Start here

1. Classify existing YAMLs with [`scripts/list_embodied_configs.py`](scripts/list_embodied_configs.py) when the user gives a config directory or repo root.
2. Statically inspect a candidate YAML with [`scripts/check_embodied_config.py`](scripts/check_embodied_config.py) before proposing a launch.
3. Use the recipe and configuration references below to reason about required paths, optional assets, overrides, log paths, video/data-collection settings, and safety constraints.

## References

- [`references/embodied-recipes.md`](references/embodied-recipes.md) — launch pattern, simulator/world-model/real-world recipe families, and model-family pairing guidance.
- [`references/embodied-api-and-config.md`](references/embodied-api-and-config.md) — embodied runner flow, worker sections, Hydra fields, model/env registries, and static YAML checks.
- [`references/realworld-and-hardware.md`](references/realworld-and-hardware.md) — Franka/XSquare/DOSW1/GimArm style prerequisites, safety gates, control-node topology, teleoperation, and real-world data collection.
- [`references/reward-data-and-offline.md`](references/reward-data-and-offline.md) — episode collection, reward-model datasets, VLM Trend rewards, replay buffers, D4RL/offline RL, RECAP/STEAM/CFG, and VLA/VLM SFT intersections.
- [`references/troubleshooting.md`](references/troubleshooting.md) — simulator assets, EGL/MuJoCo, `ROBOT_PLATFORM`, optional dependencies, Ray worker failures, data-collection mistakes, reward worker issues, and hardware safety triage.

## Routing boundaries

- Ray startup, multi-node environment variables, and placement syntax details belong to `setup-and-cluster`; this skill only says which embodied components must be placed and what assumptions to check.
- Standalone evaluation, checkpoint resume/inspection, TensorBoard/W&B/SwanLab operations, and debug-log interpretation belong to `operations-evaluation-debugging`.
- Adding new environment/model source code, registries, workers, tests, Docker, or CI belongs to `extension-development`.

## Safety defaults

- Prefer static checks and small YAML reviews over real launches.
- Treat real robot movement as a high-risk operation requiring an operator, workspace clearance, e-stop readiness, calibrated cameras/grippers, correct robot IP/serials, and explicit user approval.
- Do not suggest ad-hoc hardware checks on a live robot; use dummy/simulation configs or read-only topology review unless the user explicitly asks for a controlled hardware validation.
