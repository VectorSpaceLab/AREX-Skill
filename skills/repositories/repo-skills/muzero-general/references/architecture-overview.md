# Architecture Overview

## Purpose

Read this to understand how MuZero General's modules fit together before editing commands, configs, networks, MCTS, checkpoints, or diagnostics.

## Bundled source shape

MuZero General is an upstream source-checkout style Python project, so this skill includes a self-contained source snapshot under `runtime/source/`. Core modules live in `runtime/source/` and game wrappers live under `runtime/source/games/`. Skill-owned entry points add this directory to `sys.path` automatically; an external checkout is optional, not required for core workflows.

| Area | Role |
| --- | --- |
| `runtime/source/muzero.py` | Main user-facing API/CLI. Imports `games.<name>`, applies config overrides, initializes Ray, creates workers, trains/tests, loads checkpoints, launches HPO, and exposes an interactive menu. Prefer skill-owned `scripts/run_muzero.py` for non-interactive execution. |
| `runtime/source/games/*.py` | Built-in games and `MuZeroConfig` classes. Each game module defines the game contract, action/observation shape, players, network defaults, training scale, replay settings, and optional dependencies. |
| `runtime/source/models.py` | PyTorch network factory and FC/ResNet implementations. Also owns value/reward scalar support transforms. |
| `runtime/source/self_play.py` | Ray `SelfPlay` actor, MCTS, tree `Node`, `GameHistory`, and `MinMaxStats`. Generates search statistics and game histories. |
| `runtime/source/trainer.py` | Ray `Trainer` actor. Pulls replay batches, runs unrolled network predictions, computes value/reward/policy losses, applies optimizer updates, and updates shared storage. |
| `runtime/source/replay_buffer.py` | Ray replay buffer actor and optional reanalyse actor. Stores game histories, samples positions/games, computes targets, and updates PER priorities. |
| `runtime/source/shared_storage.py` | Ray actor that stores the current checkpoint dict and saves `model.checkpoint`. |
| `runtime/source/diagnose_model.py` | Diagnostic helpers for virtual-vs-real trajectory comparison and optional MCTS graph/heatmap plotting. |

## High-level lifecycle

1. `MuZero(game_name, config=None, split_resources_in=1)` imports `games.<game_name>`, builds default config, applies overrides, seeds NumPy/Torch, validates GPU flags, starts Ray, and initializes model weights.
2. `MuZero.train(log_in_tensorboard=True)` creates Ray actors for trainer, shared storage, replay buffer, optional reanalyse, and self-play workers.
3. Self-play workers run MCTS against game wrappers and send `GameHistory` objects to replay buffer.
4. Replay buffer samples histories/positions and constructs value, reward, policy, action, and gradient-scale targets.
5. Trainer consumes batches, calls model initial/recurrent inference, computes losses, updates weights, and writes new weights/losses to shared storage.
6. Shared storage saves checkpoints when configured.
7. TensorBoard logging uses a test self-play worker and shared storage metrics.
8. `MuZero.test(...)` creates a temporary self-play worker to play evaluation games.
9. `MuZero.load_model(...)` can load `model.checkpoint` and `replay_buffer.pkl` before training or testing.
10. Diagnostics can compare model-predicted trajectories against real game transitions when a compatible checkpoint/config is available.

## Data contracts between modules

- Game observations are 3D arrays shaped like `config.observation_shape`.
- Action spaces are integer lists, normally `list(range(n))`.
- `GameHistory` stores observation, action, reward, to-play, child-visit, root-value, and optional reanalysed-value sequences.
- Model inference returns `(value, reward, policy_logits, hidden_state)` where value/reward are support logits.
- MCTS root expansion masks `policy_logits` to legal actions, then later expands leaves over the full action space.
- Checkpoints are dictionaries containing weights, optimizer state, counters, losses, rewards, and `terminate`.

## Where to route deeper questions

- CLI/API run planning and Ray/TensorBoard runtime: `sub-skills/training-and-cli/SKILL.md`.
- Game wrapper and `MuZeroConfig` authoring: `sub-skills/games-and-configs/SKILL.md`.
- Tensor shapes, FC/ResNet, support transforms, and MCTS internals: `sub-skills/models-and-mcts/SKILL.md`.
- Checkpoint/replay/diagnostic artifacts: `sub-skills/checkpoints-and-diagnostics/SKILL.md`.
