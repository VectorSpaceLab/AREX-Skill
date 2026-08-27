---
name: offline-rl
description: "Use AI-Optimizer's offline RL algorithms, d3rlpy-derived APIs,
  MDPDataset flows, and offline-to-online E2O/PEX workflows safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# offline-rl

Use this sub-skill when a task mentions AI-Optimizer offline RL, batch RL, D4RL datasets, `MDPDataset`, d3rlpy-style APIs, BCQ, BEAR, CQL, AWAC, REDQ, UWAC, ISPI, COMBO, MOPO, E2O, PEX, or offline-to-online RL.

Do not use this sub-skill for model-based online RL outside the offline COMBO/MOPO workflows, or for multi-agent RL; route those tasks to the sibling `model-based-rl` or `multi-agent-rl` sub-skills.

## Start here

- Read `references/offline-rl-overview.md` to choose the algorithm family and understand the PC/VR/MB/U/Off2On taxonomy.
- Read `references/offline-training-workflows.md` before forming command lines for BCQ, BEAR, CQL, AWAC, REDQ, UWAC, ISPI, COMBO, or MOPO.
- Read `references/e2o-pex-workflows.md` for E2O and Policy Expansion offline-to-online workflows.
- Read `references/dataset-and-d3rlpy-api.md` before creating or validating custom datasets or instantiating d3rlpy-derived algorithm classes.
- Read `references/troubleshooting.md` before attempting simulator, D4RL, MuJoCo, Waymo, PyTorch, Gym, or checkpoint-heavy workflows.

## Bundled safe helpers

These helpers are static and safe by default: they build or validate local inputs and never launch training, download datasets, mutate environments, or write model outputs.

- `scripts/build_offline_rl_command.py` prints shell-quoted command recipes for BCQ, BEAR, CQL, AWAC, REDQ, UWAC, ISPI, COMBO, and MOPO, including the correct dataset/env flag family.
- `scripts/build_pex_command.py` prints shell-quoted PEX offline or online command recipes, including checkpoint and evaluation flags.
- `scripts/validate_mdp_dataset_npz.py` validates local `.npz` arrays before converting them to an `MDPDataset`-style flow.

## Operating constraints

- Treat full RL training, D4RL/MuJoCo/Waymo acquisition, CUDA execution, and long benchmark runs as task-specific prerequisites, not as capabilities already proven by this skill.
- Prefer static command construction and dataset schema validation before any expensive training attempt.
- Keep algorithm-specific script flag differences explicit: many offline scripts use `--dataset`, REDQ and ISPI use `--env`, PEX uses `--env_name`, and GPU flags are not uniform.
- For custom datasets, validate array shapes and terminal/timeout semantics before fitting an algorithm.
- For offline-to-online runs, require a deliberate checkpoint handoff from offline training to online fine-tuning; never assume a checkpoint exists.
