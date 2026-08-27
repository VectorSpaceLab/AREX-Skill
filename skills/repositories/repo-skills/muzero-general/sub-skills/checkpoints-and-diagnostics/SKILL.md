---
name: checkpoints-and-diagnostics
description: "Inspects and troubleshoots MuZero General checkpoints, replay
  buffers, TensorBoard artifacts, and model-dynamics diagnostics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Checkpoints and Diagnostics

Use this sub-skill when the task is to load or inspect `model.checkpoint`, reason about `replay_buffer.pkl`, avoid checkpoint/config mismatches, understand `results/<game>/<timestamp>/`, run non-interactive diagnostics, or troubleshoot Graphviz/matplotlib/TensorBoard artifacts.

## Fast route

1. Read [checkpoints-and-diagnostics.md](references/checkpoints-and-diagnostics.md) for checkpoint schema, save/load paths, replay buffer fields, `DiagnoseModel` methods, TensorBoard artifacts, and safe headless workflows.
2. Read [troubleshooting.md](references/troubleshooting.md) when paths are invalid, `torch.load` fails, weights do not match the selected config/network, replay buffer loading fails, Graphviz is missing, or plotting blocks a headless session.
3. Inspect a checkpoint without running a model:

   ```bash
   python sub-skills/checkpoints-and-diagnostics/scripts/inspect_checkpoint.py --checkpoint <model.checkpoint> --json
   ```

4. Before calling `MuZero.load_model(...)`, confirm the intended game/config in [games-and-configs](../games-and-configs/SKILL.md) and model shape compatibility in [models-and-mcts](../models-and-mcts/SKILL.md).

## Scope and routing boundaries

This sub-skill owns:

- `MuZero.load_model(checkpoint_path=None, replay_buffer_path=None)` behavior.
- `SharedStorage.save_checkpoint(path=None)` and default `model.checkpoint` paths.
- Checkpoint dict keys, counters, weight state dicts, optimizer state, and replay buffer pickle metadata.
- `DiagnoseModel` and `Trajectoryinfo` usage boundaries.
- Optional Graphviz and plotting dependencies.
- Safe non-interactive checkpoint inspection and headless diagnostic planning.

Route elsewhere when the task is primarily about:

- Producing checkpoints through training, TensorBoard logging loop, or CLI commands: [training-and-cli](../training-and-cli/SKILL.md).
- Choosing game/config fields for checkpoint compatibility: [games-and-configs](../games-and-configs/SKILL.md).
- Interpreting network tensor shape, support size, or MCTS internals: [models-and-mcts](../models-and-mcts/SKILL.md).

## Safe defaults

- Use `torch.load(..., map_location="cpu")` for inspection unless the user explicitly wants GPU loading.
- Do not bundle or depend on source `results/` binary checkpoints; they are evidence of schema and naming only.
- Do not call `MuZero.diagnose_model` in automation; it calls plotting paths and then waits for input.
- Prefer `DiagnoseModel(...).compare_virtual_with_real_trajectories(..., plot=False)` only after a matching config/game/checkpoint is loaded and a real observation is available.

## Compatibility checklist

Before loading a checkpoint for testing or diagnostics:

- Game module matches the checkpoint's architecture assumptions.
- `network`, `support_size`, `observation_shape`, `action_space`, `stacked_observations`, `channels`/`encoding_size`, and downsample fields match the saved weights.
- Replay buffer, if loaded, was produced by the same or compatible game/config.
- Paths point to files, not directories.
- Optional plotting dependencies are installed only when plots are needed.
