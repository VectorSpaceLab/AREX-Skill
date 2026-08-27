---
name: evaluation-and-persistence
description: "Evaluate Stable-Baselines3 policies, configure callbacks/logging,
  save/load models and auxiliary state, transfer parameters, and debug
  portability issues."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Evaluation and Persistence

Use this sub-skill when the task is about measuring policy quality, configuring evaluation/checkpoint callbacks, logging training/evaluation metrics, saving or loading SB3 artifacts, inspecting save files, transferring weights, or making loaded models portable across machines/devices.

## Start here

- For `evaluate_policy`, `EvalCallback`, `CheckpointCallback`, `BaseCallback`, and frequency caveats, read [evaluation-and-callbacks.md](references/evaluation-and-callbacks.md).
- For `save()`, `load()`, SB3 zip contents, `custom_objects`, `print_system_info`, replay buffers, `VecNormalize`, and parameter transfer, read [save-load.md](references/save-load.md).
- For default logger behavior, TensorBoard, progress bars, custom scalar/image/video logging, and logger output names, read [logging.md](references/logging.md).
- For verified signatures and import paths, read [api-reference.md](references/api-reference.md).
- For common failure modes and portability triage, read [troubleshooting.md](references/troubleshooting.md).
- To evaluate an existing `.zip` model without bundled checkpoints, use [scripts/evaluate_saved_model.py](scripts/evaluate_saved_model.py).

## Boundaries

- Use other sub-skills for choosing algorithms/training hyperparameters, creating custom environments/vectorization stacks, or designing custom policies/networks.
- This sub-skill assumes the environment and algorithm choice are already known and focuses on evaluation, callbacks, logging, persistence, and replay/normalization state.
