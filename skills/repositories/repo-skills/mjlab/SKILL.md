---
name: mjlab
description: "Use mjlab for MuJoCo Warp robot-learning environments,
  manager-based MDP configuration, RSL-RL training/playback, sensors, terrain,
  and debugging workflows."
metadata:
  disco-role: operating
  scenarios:
    - reinforcement-learning-workflows
    - embodied-ai-simulation
disable-model-invocation: true
license: Apache 2.0
---

# mjlab

mjlab is a lightweight robot-learning framework that brings an Isaac Lab-style
manager API to MuJoCo Warp. Use this repo skill when a task involves composing
robot simulation scenes, writing manager-based RL environments, configuring MDP
terms, training or playing policies with RSL-RL, using cameras/raycasts/contact
sensors, generating terrain, exporting scenes, or debugging NaNs/rendering.

## Fast orientation

- Package/import name: `mjlab`.
- Public command surface: `train`, `play`, `demo`, `list-envs`, `export-scene`,
  and `viz-nan`.
- Primary runtime: Linux with NVIDIA CUDA for training and full MuJoCo Warp
  throughput. CPU mode is useful for config loading, CLI help, and some
  evaluation/debugging tasks; it is not proof of full GPU training behavior.
- CLI parsing uses Tyro: boolean values must be explicit and collection values
  use Python-literal syntax.

Read [installation-runtime.md](references/installation-runtime.md) before
installing or choosing CPU/GPU/Docker execution. Read
[package-overview.md](references/package-overview.md) for the architectural map
and high-value entry points. Read
[troubleshooting.md](references/troubleshooting.md) for cross-cutting install,
backend, CLI, rendering, W&B, and data issues. Use
[scripts/mjlab_environment_smoke.py](scripts/mjlab_environment_smoke.py) for a
safe installed-package smoke check.

## Route by task

| If the user asks about... | Read this |
|---|---|
| `ManagerBasedRlEnvCfg`, observation/reward/event/command dictionaries, term lifecycle, reset/step ordering, `SceneEntityCfg`, custom manager terms | [environment-configuration](sub-skills/environment-configuration/SKILL.md) |
| `SceneCfg`, `EntityCfg`, MJCF/spec editing, simulation config, asset-zoo robots, variants, scene export API internals | [scene-simulation-assets](sub-skills/scene-simulation-assets/SKILL.md) |
| action configs, actuator configs, built-in observations/rewards/terminations/events/commands/curriculum/metrics, differential IK, task-specific MDP terms | [mdp-components](sub-skills/mdp-components/SKILL.md) |
| cameras, raycasts, contacts, terrain generation, flat patches, terrain curricula, domain randomization, sensor context or rendering issues | [perception-terrain-randomization](sub-skills/perception-terrain-randomization/SKILL.md) |
| `list-envs`, `train`, `play`, `demo`, `export-scene`, `viz-nan`, task registry, RSL-RL configs, checkpoints, W&B, motion CSV/NPZ, cloud/distributed training | [training-evaluation-cli](sub-skills/training-evaluation-cli/SKILL.md) |

## Safe first commands

Use the installed package, not a source checkout, for normal user workflows:

```bash
uv run list-envs
uv run train Mjlab-Cartpole-Balance --help
uv run play Mjlab-Cartpole-Balance --help
uv run export-scene g1 --help
```

For package-level verification from any project that has mjlab installed, copy
this skill's smoke script into a temporary location or run it by path:

```bash
uv run python path/to/mjlab_environment_smoke.py --json
```

## Installation decision points

- For a new uv-managed user project, prefer `uv add mjlab`.
- For contributing to mjlab itself, use `uv sync` and invoke commands with
  `uv run`.
- For Linux NVIDIA training, use the CUDA-capable dependency variant selected
  by the project environment or a Docker image with the NVIDIA container
  runtime.
- For macOS or CPU-only machines, limit expectations to evaluation, config
  inspection, CLI help, and workflows that do not require CUDA graph capture.

## Do not use this skill when

- The task is about a generic RL algorithm library unrelated to mjlab's
  environment/runtime layer.
- The task requires Isaac Sim or Omniverse APIs rather than MuJoCo/MuJoCo Warp.
- The user is asking for benchmark systemd jobs, W&B sweeps, or cloud launches
  without explicitly authorizing credentials, network access, and GPU cost.
- The user is editing this repository's code as a maintainer task; then combine
  this operating skill with normal repository-maintenance evidence and tests.

## Provenance and routing metadata

- [repo-provenance.md](references/repo-provenance.md) records the source commit,
  tag, package version, and evidence baseline used to create this skill.
- [repo-routing-metadata.json](references/repo-routing-metadata.json) is the
  structured import metadata for the managed repo-skills router.
