---
name: off-policy-continuous-control
description: "Route and operate the repo's DDPG, SAC, TD3 continuous-action
  workflows, checkpoint playback, Gym compatibility, action scaling, and backend
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Off-Policy Continuous Control

Use this sub-skill when the task is about this repository's continuous-action, off-policy examples: DDPG, SAC, TD3, saved-policy playback, normalized continuous actions, Pendulum, or BipedalWalker.

Do **not** use this sub-skill for tabular control, DQN/discrete value control, or on-policy actor-critic/PPO/A2C requests. Route those to sibling sub-skills such as `../tabular-control/`, `../value-based-discrete-control/`, or `../on-policy-actor-critic/` when available.

## First-read references

- Read `references/workflow-guide.md` to choose between DDPG, SAC, SAC dual-Q, SAC BipedalWalker, TD3, and TD3 BipedalWalker variants.
- Read `references/checkpoint-playback.md` before any `--mode test`, saved checkpoint, or model-load task.
- Read `references/troubleshooting.md` whenever the request mentions CUDA/CPU selection, action bounds, checkpoint paths, Gym deprecations, Box2D, pygame, rendering, or NumPy compatibility.
- Use `scripts/continuous_control_compat_report.py` for a local, non-training compatibility report on torch device availability, Gym env IDs, Box2D/pygame readiness, and continuous-action bounds.

## Routing by user request

| Request signal | Best route | Key cautions |
| --- | --- | --- |
| "run DDPG on Pendulum" | DDPG workflow in `references/workflow-guide.md` | Modern Gym uses `Pendulum-v1`, while repo defaults name `Pendulum-v0`; training is long-running and checkpoint path changes with env id. |
| "train SAC" / "compare SAC variants" | SAC workflow table | `SAC.py` is single-Q Pendulum-only and has a broken load method; dual-Q scripts are closer to the later SAC variants. |
| "test a SAC checkpoint" | `references/checkpoint-playback.md` | Requires a matching `SAC_model/` directory and the same env/action dimensionality used at training time. |
| "compare SAC vs TD3" | Compare `references/workflow-guide.md` algorithm rows | TD3 uses direct bounded actions; SAC scripts wrap actions through a normalized action wrapper that needs a modern Gym patch. |
| "BipedalWalker compatibility" | BipedalWalker notes in both references | Prefer `BipedalWalker-v3`; verify Box2D and pygame before running render or checkpoint playback. |
| "CartPole, MountainCar DQN, Q-learning" | Different sub-skill | Those are discrete or tabular workflows, not this continuous-control owner. |

## Operating rules

1. Treat the original training scripts as reference-backed workflows, not safe bundled trainers. They run large episode counts by default, may render, save under relative experiment directories, and assume old Gym APIs.
2. Before suggesting a run command, decide whether the caller wants inspection, bounded smoke, training, or checkpoint playback. Ask for a time/episode budget before launching training-scale loops.
3. Modernize legacy environment IDs unless the caller explicitly pins an old Gym stack:
   - `Pendulum-v0` -> `Pendulum-v1`
   - `BipedalWalker-v2` -> `BipedalWalker-v3`
4. Keep continuous actions in the environment's Box bounds. DDPG/TD3 actors output `tanh * max_action`; SAC variants sample normalized actions in `[-1, 1]` and rely on an action wrapper to map to environment bounds.
5. Do not assume a checkpoint exists. Explain expected filenames and relative directory conventions before playback.
6. Prefer CPU-compatible guidance unless the user requests CUDA performance. The scripts choose `cuda` when `torch.cuda.is_available()` is true; see troubleshooting for how to force or debug device behavior.

## Safe helper

From this sub-skill directory, run:

```bash
python scripts/continuous_control_compat_report.py --env Pendulum-v1 --env BipedalWalker-v3
```

Use `--step` only for a tiny random-action step smoke. The helper does not train, read checkpoints, or require the original source checkout.
