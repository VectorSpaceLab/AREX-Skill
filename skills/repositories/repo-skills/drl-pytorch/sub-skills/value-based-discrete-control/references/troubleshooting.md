# Value-Based Troubleshooting

Use this reference when DRL-Pytorch value-based workflows fail before training, during a safe smoke, while loading checkpoints, or after a short stochastic run.

## Quick symptom table

| Symptom | Likely cause | Recovery |
|---|---|---|
| `AssertionError: Torch not compiled with CUDA enabled`, CUDA device error, or GPU allocation failure | Several launchers default to CUDA (`--dvc cuda`), and PER Gymnasium 0.2x chooses CUDA automatically when visible. | For DQN/C51/NoisyNet pass `--dvc cpu`. For PER start Python with `CUDA_VISIBLE_DEVICES=""`. Re-run a zero-step smoke before training. |
| `gymnasium.error.NameNotFound` or Box2D import/build errors for LunarLander | `--EnvIdex 1` selects `LunarLander-v2`, which requires optional Box2D support. | Use `--EnvIdex 0` for a base CartPole smoke, or install/test `gymnasium[box2d]` in the active environment before LunarLander. |
| `ModuleNotFoundError: DQN`, `utils`, `LPRB`, `PriorDQN`, or the wrong class appears | Algorithm directories are standalone and have colliding local module names. | Run the launcher from its own directory. For Python diagnostics, isolate one directory on `sys.path` and purge colliding module names before switching algorithms; [smoke_value_based.py](../scripts/smoke_value_based.py) does this. |
| `FileNotFoundError` for `model/...pth` or `model/q_table.npy` | Checkpoint paths are relative to current working directory, and `ModelIdex` must match the naming convention. | Run from the algorithm directory containing `model/`, or create/pass the expected checkpoint. Check whether the workflow uses raw step counts, thousands, or a `k` suffix. |
| `tensorboard: command not found` or no curves appear | TensorBoard is not installed, `--write` was false, or logs were written under another working directory. | Install TensorBoard in the active environment, run training with `--write True`, then run `tensorboard --logdir runs` from the directory that owns the generated `runs/`. |
| Legacy PER breaks on Gymnasium 0.29 / Python 3.11 | `PriorDQN_gym0.1x` targets gym 0.19 and the old step API. | Prefer `LightPriorDQN_gym0.2x` or `PriorDQN_gym0.2x`. Use the legacy folder only in an intentionally old Python 3.9 + gym 0.19 environment. |
| Tensor shape or dtype errors in replay buffer add/sample | State shape, action dtype, or terminal flag dtype does not match the implementation. | For vector envs, pass 1-D NumPy states shaped `(state_dim,)`; actions are integer discrete ids; DQN/C51/Noisy replay stores `dw` as boolean; PER sum-tree stores `dw` numerically and casts on sample. |
| Training score varies wildly or seems worse than expected | RL training is stochastic; defaults are long and use warm-up/random exploration, noise schedules, and periodic target updates. | First validate with zero-step or bundled smoke, then run multiple seeds and enough steps. Do not judge algorithm correctness from a tiny training budget. |

## CPU recovery commands

DQN, C51, and NoisyNet support explicit CPU selection:

```bash
python main.py --dvc cpu --EnvIdex 0 --write False --render False --Max_train_steps 0
```

PER launchers do not have `--dvc`; hide CUDA before process start:

```bash
CUDA_VISIBLE_DEVICES="" python main.py --EnvIdex 0 --write False --render False --Max_train_steps 0
```

If the zero-step command fails on `--EnvIdex 1`, verify Box2D separately or switch to `--EnvIdex 0` to distinguish algorithm/import issues from optional environment issues.

## Working directory and checkpoint recovery

The launchers use relative paths:

- `model/` is created in the current working directory;
- `runs/` is created in the current working directory when `--write True`;
- `Loadmodel` uses `torch.load` or `np.load` against relative model paths.

Checkpoint naming traps:

- DQN family saves `DuelDDQN_CPV1_100.pth`-style names where `100` means 100k training steps.
- LightPrior PER also saves thousands (`DDQN_CPV1_250.pth`).
- Sum-tree PER saves raw step counts (`DDQN_CPV1_50000.pth`).
- C51 and NoisyNet include a literal `k` suffix before `.pth` (`C51_DDQN_CPV1_60k.pth`, `NoisyNetDQN_CPV1_100k.pth`).
- Tabular Q-learning uses `q_table.npy`, not a PyTorch checkpoint.

If play mode cannot find a checkpoint, confirm the current directory, `EnvIdex`, algorithm flags, and `ModelIdex` all reconstruct the same file name.

## Render and play mode traps

- DQN and NoisyNet render/play mode enters an infinite evaluation loop when `--render True`; stop it manually when done.
- C51 render mode calls a Matplotlib distribution visualizer and needs Matplotlib in addition to Gymnasium.
- PER render mode performs a fixed evaluation rather than training, but still needs the checkpoint when `--Loadmodel True`.
- Avoid render mode in automated smoke checks; use `--render False --Max_train_steps 0` or the bundled diagnostic.

## PER-specific notes

LightPrior PER stores only the current state and derives `s_next` from the next stored state. It avoids sampling invalid boundary indices and masks truncated transitions in the loss. If a custom buffer probe fails, ensure at least several sequential records have been added and that priorities are positive.

Sum-tree PER initializes new priorities from current max priority and updates priorities after TD-error computation. If all priorities are zero or sampling returns invalid weights, add initial transitions through the buffer's `add` method rather than mutating arrays directly.

## C51-specific notes

C51's categorical projection uses `v_min`, `v_max`, and `n_atoms`; unreasonable support bounds can clip returns heavily. For custom tasks, set value support according to expected return scale. The default `[-100, 100]` with 51 atoms matches the bundled CartPole/LunarLander examples.

## NoisyNet-specific notes

NoisyNet exploration comes from `NoisyLinear` layers. In training mode, the noisy layer resets sampled noise on each forward pass; in eval mode it uses mean weights. If actions look non-reproducible during training diagnostics, switch the network to eval mode for deterministic forward checks.

## Use the bundled smoke first

For a no-training diagnostic:

```bash
python scripts/smoke_value_based.py --repo-root <DRL-Pytorch-checkout> --algorithm all
```

This validates imports, a tiny Q-learning update, and dummy network/buffer checks without creating Gym environments, downloading data, or launching training loops.
