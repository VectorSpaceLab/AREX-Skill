# Checkpoints and Diagnostics Reference

## Purpose

Read this when loading checkpoints, replay buffers, or diagnostic plots with the skill-bundled MuZero General source snapshot or an explicitly staged copy. The facts here are distilled from `muzero.py`, `shared_storage.py`, `diagnose_model.py`, README checkpoint claims, the notebook, and the prepared inspection environment.

## Checkpoint locations and naming

The repository writes checkpoints and replay buffers under a timestamped results path when `save_model` or TensorBoard logging is enabled:

```text
results/<game>/<YYYY-MM-DD--HH-MM-SS>/model.checkpoint
results/<game>/<YYYY-MM-DD--HH-MM-SS>/replay_buffer.pkl
```

The README also advertises pretrained weights under `results/`. Treat those files as evidence of the schema and naming convention; do not require them to exist in a generated skill tree.

## Checkpoint schema

`MuZero` and `SharedStorage` share a checkpoint dictionary with these keys:

- `weights`
- `optimizer_state`
- `total_reward`
- `muzero_reward`
- `opponent_reward`
- `episode_length`
- `mean_value`
- `training_step`
- `lr`
- `total_loss`
- `value_loss`
- `reward_loss`
- `policy_loss`
- `num_played_games`
- `num_played_steps`
- `num_reanalysed_games`
- `terminate`

The initial constructor snapshot populates these fields and then Ray workers update them during training.

## `MuZero.load_model`

Verified signature:

```python
load_model(checkpoint_path=None, replay_buffer_path=None)
```

Behavior:

- When `checkpoint_path` is set, it loads the checkpoint with `torch.load(path)` and prints the path used.
- When `replay_buffer_path` is set, it unpickles `replay_buffer.pkl`, restores the buffer, and copies `num_played_steps`, `num_played_games`, and `num_reanalysed_games` into the checkpoint.
- When only a checkpoint is loaded, it prints `Using empty buffer.` and resets counters to zero for a fresh run.

## `SharedStorage.save_checkpoint`

Verified signature:

```python
save_checkpoint(path=None)
```

Behavior:

- Uses `config.results_path / "model.checkpoint"` when `path` is omitted.
- Saves the current checkpoint dict with `torch.save`.

## Replay buffer pickle schema

`MuZero.train` persists `replay_buffer.pkl` as a pickle dict containing:

- `buffer`: the replay buffer dictionary keyed by game id.
- `num_played_games`
- `num_played_steps`
- `num_reanalysed_games`

Use this file only when you need to resume or inspect training state. It is separate from `model.checkpoint`.

## `DiagnoseModel` behavior

Verified signature highlights:

- `DiagnoseModel(checkpoint, config)`
- `get_virtual_trajectory_from_obs(observation, horizon, plot=True, to_play=0)`
- `compare_virtual_with_real_trajectories(first_obs, game, horizon, plot=True)`
- `plot_mcts(root, plot=True)`

Behavior notes:

- Loads the model weights from the supplied checkpoint into a `MuZeroNetwork` on CPU if CUDA is unavailable.
- Uses `MCTS.run` to build virtual and real trajectories.
- `plot_mcts` tries to import `graphviz.Digraph` and renders a PDF named `mcts.pdf` in the working directory when plotting is enabled.
- `compare_virtual_with_real_trajectories` can call `input("Press enter to close all plots")` through `MuZero.diagnose_model`; avoid that wrapper in automation.

## Headless-safe diagnostics workflow

1. Use `inspect_checkpoint.py` to inspect checkpoint keys before loading.
2. Confirm the game/config and model architecture in sibling `games-and-configs` and `models-and-mcts`.
3. Load the checkpoint on CPU with `torch.load(map_location="cpu")` if only schema inspection is needed.
4. For non-plot model comparison, instantiate `DiagnoseModel(checkpoint, config)` and call the comparison method with `plot=False` only after you already have a compatible live `game` instance and an initial observation.
5. Install Graphviz only when a plot is genuinely needed.

## Compatibility warnings

- `torch.load` on a mismatched checkpoint/config can fail or silently load incompatible weights into a wrong architecture.
- A checkpoint saved with one `support_size`, `network`, `channels`, `encoding_size`, `observation_shape`, or `action_space` is generally not interchangeable with a different architecture.
- Replay buffers are game/config dependent because their targets and histories encode game-specific action/observation semantics.
- Do not read binary checkpoint contents with the original repository still assumed to be present; the generated skill should explain the schema independently.
