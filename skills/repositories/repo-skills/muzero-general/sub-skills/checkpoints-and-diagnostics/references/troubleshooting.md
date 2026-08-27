# Checkpoints and Diagnostics Troubleshooting

## Checkpoint path is invalid

Symptoms:

- `Invalid checkpoint path. Try again.` in the interactive menu.
- `FileNotFoundError` from `torch.load`.
- A directory path was supplied instead of `model.checkpoint`.

Recovery:

- Point to the actual file, usually `results/<game>/<timestamp>/model.checkpoint`.
- Use `scripts/inspect_checkpoint.py --checkpoint <file>` before calling `MuZero.load_model`.
- Avoid the interactive `load_model_menu` in automation; pass explicit paths to `load_model`.

## Replay buffer path is invalid or incompatible

Symptoms:

- `Invalid replay buffer path. Try again.`
- `pickle` load errors.
- Training resumes with inconsistent counters or target errors.

Recovery:

- Use a `replay_buffer.pkl` created by the same game/config family.
- Inspect that it contains `buffer`, `num_played_games`, `num_played_steps`, and `num_reanalysed_games`.
- If only evaluating or diagnosing weights, omit `replay_buffer_path` and let MuZero use an empty buffer.

## Weight/config mismatch

Symptoms:

- `RuntimeError` from `load_state_dict` about missing, unexpected, or size-mismatched keys.
- Model inference fails after loading weights.
- Policy/value/reward head dimensions differ from expected action/support sizes.

Likely causes:

- Different `network` (`fullyconnected` vs `resnet`).
- Different `observation_shape`, `stacked_observations`, `action_space`, `support_size`, `channels`, `encoding_size`, or downsample settings.
- Checkpoint belongs to another game.

Recovery:

1. Inspect checkpoint key names with `inspect_checkpoint.py`.
2. Confirm game/config fields with `../games-and-configs/scripts/validate_game_module.py`.
3. Run `../models-and-mcts/scripts/model_mcts_smoke.py` for the intended config before loading weights.
4. If dimensions still mismatch, use the original matching game/config or retrain.

## CPU/GPU loading problems

Symptoms:

- CUDA device errors when loading a checkpoint on a CPU machine.
- GPU memory allocation failures during diagnostics.

Recovery:

- For inspection, use `torch.load(path, map_location="cpu")` or the bundled checkpoint inspector.
- For real GPU diagnostics/training, verify the environment has a CUDA-capable PyTorch and that `train_on_gpu`, `selfplay_on_gpu`, and `reanalyse_on_gpu` match available resources.

## Graphviz or plotting is missing

Symptoms:

- `Please install graphviz to get the MCTS plot.`
- No `mcts.pdf` is created.
- Matplotlib opens windows or blocks a headless job.

Recovery:

- Use `plot=False` diagnostic methods in headless automation.
- Install both the Python `graphviz` package and system Graphviz executable only when PDF MCTS plots are required.
- Set a non-interactive Matplotlib backend externally when needed.

## `MuZero.diagnose_model` blocks

`MuZero.diagnose_model(horizon)` creates a game, runs `DiagnoseModel.compare_virtual_with_real_trajectories`, then calls `input("Press enter to close all plots")`. Do not call it in unattended automation. Use lower-level `DiagnoseModel` methods with `plot=False` instead.

## Cannot infer checkpoint game with certainty

The checkpoint dict does not store a canonical game name. Weight key shapes can hint at action space, network family, and support size, but they do not always uniquely identify a game. Report uncertainty and ask for the original game/config metadata when exact loading matters.
