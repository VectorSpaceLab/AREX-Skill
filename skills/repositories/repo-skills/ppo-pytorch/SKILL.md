---
name: ppo-pytorch
description: "Routes PPO-PyTorch training, evaluation, and visualization
  workflows for the repository's PPO implementation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# PPO-PyTorch

Use this skill when the user asks about PPO training, pretrained checkpoint evaluation, reward plots, GIF creation, or the repository's shared PPO implementation.

## Start here

- Read [workflow overview](references/workflow-overview.md) to choose the right route.
- Read [dependencies and environments](references/dependencies-and-environments.md) before installing packages or choosing a legacy Gym variant.
- Run `python scripts/check_ppo_setup.py --help` for a safe import check.
- Import the bundled core module from `scripts/ppo_core.py` when you need the shared PPO classes.

## Route map

- `sub-skills/training/` — start or configure PPO training runs, log paths, checkpoints, and action-std schedules.
- `sub-skills/evaluation/` — load pretrained checkpoints, evaluate episodes, and diagnose checkpoint mismatches.
- `sub-skills/visualization/` — plot reward logs and compose GIFs from saved frames.

## Quick install

Install the core scientific stack first, then add the environment package that matches the route you want to use:

```bash
python -m pip install torch numpy
python -m pip install pandas matplotlib pillow
python -m pip install gym
```

Add a legacy environment package only when the chosen route needs it:

- `roboschool` for the shipped Roboschool checkpoints and scripts.
- `gym[box2d]` or a compatible Box2D package for `LunarLander-v2` and `BipedalWalker-v2`.
- `pybullet` only when you intentionally follow the notebook's optional alternative environment stack.

## Minimal checks

```bash
python scripts/check_ppo_setup.py
python scripts/check_ppo_setup.py --help
```

For checkpoint inspection, pass `--checkpoint-path` to the same helper or use the evaluation sub-skill helper.

## When to read the provenance file

Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill is current for a checkout or before running a refresh workflow.
