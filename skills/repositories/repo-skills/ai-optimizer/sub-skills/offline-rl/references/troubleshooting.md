# Offline RL troubleshooting

Use this page before moving from static command construction to any expensive or environment-sensitive execution.

## Dependency and backend limits

- Full offline RL training has not been established by this sub-skill alone. Treat command recipes as invocation knowledge, not proof of benchmark reproducibility.
- Most dataset-backed examples require an old Gym/D4RL/MuJoCo-compatible stack. Version mismatches are common: a modern Python/PyTorch environment may import NumPy but still fail to import D4RL, MuJoCo bindings, or legacy Gym wrappers.
- PEX declares a focused dependency set around Python 3.7+, PyTorch, Gym 0.15.4, D4RL, scipy, pandas, and tqdm. That does not mean the rest of AI-Optimizer shares one compatible environment.
- CUDA/GPU use is optional in some scripts and implicit in others. Do not use a CPU-only smoke check as evidence that GPU training works.
- Waymo datasets are mentioned as part of the offline RL ecosystem, but no Waymo dataset download or pipeline is covered by the command builders.

## Dataset failures

Common symptoms and responses:

| Symptom | Likely cause | Response |
| --- | --- | --- |
| `KeyError: observations` or similar | Custom `.npz` missing required arrays | Validate with `validate_mdp_dataset_npz.py`; require `observations`, `actions`, `rewards`, `terminals`. |
| First-dimension mismatch | Actions/rewards/terminal arrays have different numbers of transitions | Fix preprocessing before training; do not reshape blindly unless you know the transition count. |
| Episode split looks wrong | Timeout and terminal semantics were conflated | For D4RL-style data, episode boundary is usually `terminals OR timeouts`, while environment terminal remains `terminals`. |
| D4RL loader cannot find env | D4RL dependency, dataset name, or Gym registration missing | Confirm the exact dataset name and dependency stack before rerunning. |
| AntMaze scores look incomparable | Different evaluation episode counts or reward transforms | Record `eval_episode_num`, reward scaling, and environment version explicitly. |

## Script flag pitfalls

- BCQ, BEAR, CQL, AWAC, MOPO, and COMBO use dataset-name flags.
- REDQ uses `--env` and creates Gym environments for online training, despite simple examples that may look dataset-like.
- ISPI uses `--env`, has no explicit `--gpu`, and converts D4RL q-learning datasets internally.
- PEX uses `--env_name`, not `--env` or `--dataset`.
- COMBO has more than one main-looking entry in its folder. Use the COMBO-specific recipe with `--n_critics` when the requested algorithm is COMBO.
- The UWAC algorithm class exists, but a target checkout may not contain the documented trainer file. If missing, treat it as a class/API workflow rather than a script workflow.

## Training/runtime pitfalls

| Area | Risk | Mitigation |
| --- | --- | --- |
| Long runs | Default scripts can run 500k to 1M+ training steps | Require an explicit budget, log directory, and stop/restart plan. |
| Output directories | PEX refuses existing log directories; d3rlpy-style scripts write logs/checkpoints | Choose run-specific output directories before execution. |
| Checkpoint handoff | E2O/PEX online stages depend on offline artifacts | Record exact offline dataset, seed, run name, and checkpoint path before online command construction. |
| MuJoCo/D4RL | Missing simulator/data registration can fail before training | Verify imports and dataset registration separately from training. |
| GPU flags | Some scripts accept integer device IDs, REDQ uses a boolean-like flag, ISPI auto-detects CUDA | Do not standardize GPU flags across algorithms without checking the target workflow. |
| Static termination functions | MOPO/COMBO need environment-family termination functions | Confirm the dataset prefix maps to a supported static termination function. |

## Offline-to-online checkpoint compatibility

Before using an offline checkpoint online, confirm:

- same environment family and observation/action dimensions;
- same hidden layer size/count where the script constructs networks;
- same algorithm mode expected by the online stage;
- checkpoint path is a file produced by the offline stage, not just a log directory;
- evaluation episode count and max episode steps match the intended comparison.

## README-vs-script conflicts

When documentation and parser evidence conflict, trust the parser for command flags. Known conflicts or fragility:

- REDQ documentation-style examples may mention dataset-like flags, but the available parser uses `--env`.
- UWAC documentation advertises a trainer, while the algorithm class may be present without a matching train-file in the target checkout.
- PEX examples may contain a typo in the CUDA visibility environment variable; use the standard CUDA variable spelling if task-specific GPU selection is necessary.

## What this skill intentionally does not claim

- No claim of reproduced paper scores.
- No claim of successful full D4RL, MuJoCo, Waymo, CUDA, or online interaction runs.
- No guarantee that all algorithm subdirectories install together in one Python environment.
- No guarantee that external datasets can be downloaded in the user's runtime environment.
