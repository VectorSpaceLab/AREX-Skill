# Preprocessing and Devices

## Purpose

Read this when configuring the standard Breakout/Pong Atari workflows, checking
wrapper order, explaining frame/life semantics, or choosing a Torch device. This
reference distills the shared Atari helper workflow label `3-atari/env.py` into
self-contained operating guidance.

## Supported game keys and environment ids

| User-facing `--env` value | ALE/Gymnasium environment id | Notes |
| --- | --- | --- |
| `breakout` | `ALE/Breakout-v5` | Used for the documented benchmark rows. Breakout often has a `FIRE` action that must be pressed after reset/life loss. |
| `pong` | `ALE/Pong-v5` | Uses the same DQN/PPO model, preprocessing, and flags. No separate benchmark row is documented in the repository README. |

Only these two keys are part of the standard Atari sub-skill. Hard-exploration
Atari games and restore-state workflows belong to the hard-Atari route.

## CLI flags owned by the Atari helper contract

| Flag | Values / behavior | Operational guidance |
| --- | --- | --- |
| `--env` | `breakout` or `pong`; default `breakout` | Selects the ALE id above. Invalid game names should be rejected before training. |
| `--render` | Boolean | Opens a human render window during training and slows the run. Do not use on headless machines unless a display is configured. |
| `--test` | Boolean | Loads the workflow checkpoint and plays without learning. In the source workflow this also requests human rendering, so it can fail on headless systems. |
| `--device` | `auto`, `cpu`, `cuda`, `mps`; default `auto` | `auto` picks CUDA first, then Apple MPS, then CPU. Explicit unavailable backends can fail later when tensors are moved or kernels run. |
| `--wandb` | Boolean | Enables Weights & Biases logging. Omit it for offline/local runs; the workflow does not touch the network without this flag. |

## Preprocessing pipeline

The standard Atari environment pipeline is:

1. Create the ALE/Gymnasium env for the selected game with `frameskip=1`.
   This avoids double-skipping because the preprocessing wrapper below performs
   its own frame skip.
2. Apply Atari preprocessing with:
   - `noop_max=30`
   - `frame_skip=4`
   - `screen_size=84`
   - `terminal_on_life_loss=False`
   - `grayscale_obs=True`
   - `scale_obs=False`
3. If the unwrapped action meanings include `FIRE`, apply a fire-reset wrapper
   that takes action `1` once after reset. This prevents Breakout-like games
   from wasting many frames waiting for a random launch action.
4. Apply a life-loss terminal wrapper that marks life loss as terminal for
   bootstrapping but does not reset the real game until game-over.
5. Apply a 4-frame stack wrapper. The resulting observation contract is a
   stack of four grayscale `84 x 84` `uint8` frames, normally shaped
   `(4, 84, 84)` for single-env model input.

Model code should normalize observations inside the network (`x.float() / 255`)
rather than asking the preprocessing wrapper to emit floating point images. This
keeps replay and rollout storage smaller.

## Life-loss versus game-over returns

The Atari helper intentionally separates two return concepts:

- **Per-life return** resets every time the life-loss wrapper emits a terminal
  transition. This is useful for DQN targets and PPO GAE because the value chain
  should not bootstrap across a death.
- **Per-game return** accumulates across all lives until the real ALE game is
  over. The wrapper sets `info["game_over"]` so the training loop can decide
  whether to reset the game-level accumulator.

When a user asks why `recent_mean_return` differs from
`recent_mean_game_return`, explain that the former is per-life and the latter is
per-game. Benchmark rows in the README use final mean **per-game** return over
the last 20 training episodes/games, not the per-life statistic.

## Vectorization for PPO

The PPO Atari workflow uses `SyncVectorEnv` with eight copies of the same
preprocessed env. The vector observation shape is therefore
`(n_envs, 4, 84, 84)`, where the default `n_envs` is `8`. The source workflow
handles per-life and per-game accumulators per environment.

Use synchronous vectorization here; do not infer that this standard Breakout/Pong
workflow uses envpool, deterministic restore states, or the hard-exploration
runner. Those are separate hard-Atari concepts.

## Device selection and caveats

Device selection priority for `--device auto` is:

1. `cuda` if `torch.cuda.is_available()` is true.
2. `mps` if `torch.backends.mps.is_available()` is true.
3. `cpu` otherwise.

Practical notes:

- CPU is acceptable for smoke checks and debugging, but 10M-step Atari training
  is slow.
- CUDA/MPS acceleration changes wall-clock time but does not remove the need for
  ROMs, RAM for replay/rollouts, and a long run budget.
- Explicit `--device cuda` or `--device mps` should be treated as a hard user
  request. If the backend is unavailable or an operation is unsupported, recover
  by switching to `--device auto` or `--device cpu`, or by preparing the correct
  Torch/backend build.
- The bundled smoke helper accepts the same device vocabulary but uses only
  synthetic tensors, so it is the safest first check for model/replay/GAE logic.

## Dependencies and assets

For real ALE env creation, the workflow needs Python 3.11-era dependencies such
as Torch, Gymnasium with Atari support, `ale-py`, NumPy, and Pygame. Actual env
reset/training/test also requires Atari ROM availability under the user's valid
license path or accepted ROM-installation workflow. W&B credentials are required
only when `--wandb` is used.

The bundled smoke helper does **not** require Gymnasium, ALE, ROMs, Pygame,
W&B, network access, or a display; it only needs NumPy and Torch.
