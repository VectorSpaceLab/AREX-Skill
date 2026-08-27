---
name: training-and-evaluation
description: "Compose and debug Diffusion Policy Hydra training, evaluation, Ray
  multirun, checkpoint evaluation, and benchmark logging commands."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Training and Evaluation

Use this sub-skill when you need to build or debug Diffusion Policy training and evaluation workflows.

## Route here for

- Single-seed Hydra training from `train.py`.
- Checkpoint evaluation from `eval.py`.
- Ray multirun orchestration from `ray_train_multirun.py` and `ray_exec.py`.
- Offline aggregation of `train_*/logs.json.txt` from `multirun_metrics.py`-style logs.
- Simulation benchmark routing for low-dim, image, hybrid, Robomimic, and video workspaces.
- W&B, checkpoint, and output-tree diagnostics for training/evaluation runs.

## Do not handle here

- Dataset zarr schema, conversion, replay-buffer layout, or sampling details: route to [data-and-replay-buffers](../data-and-replay-buffers/).
- Policy/model architecture, losses, normalizers, or inference internals: route to [policies-and-models](../policies-and-models/).
- UR5, RealSense, SpaceMouse, or live robot execution: route to [real-robot-operations](../real-robot-operations/).

## Operating workflow

1. Choose the workspace config family and matching task config.
2. Compose the resolved config with [`scripts/compose_experiment_config.py`](scripts/compose_experiment_config.py).
3. Launch a single-seed `train.py` run or a Ray multirun.
4. Inspect `logs.json.txt`, checkpoints, `eval_log.json`, and `metrics/logs.json.txt`.
5. Use [`scripts/summarize_multirun_metrics.py`](scripts/summarize_multirun_metrics.py) to summarize finished `train_*` logs offline.

## Core API names

- `BaseWorkspace.run()` drives the training/evaluation lifecycle.
- `BaseWorkspace.save_checkpoint()` and `BaseWorkspace.load_checkpoint()` manage checkpoint state.
- `policy.set_normalizer(...)` and `policy.predict_action(...)` are the key policy hooks.
- `env_runner.run(policy)` produces rollout metrics and videos.
- `JsonLogger`, `read_json_log`, and `TopKCheckpointManager` shape the run logs.

## Start here

Read the bundled references for command recipes, config structure, and troubleshooting:

- [training-and-evaluation](references/training-and-evaluation.md)
- [configuration](references/configuration.md)
- [troubleshooting](references/troubleshooting.md)
