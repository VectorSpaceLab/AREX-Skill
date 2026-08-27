---
name: muzero-general
description: "Guides MuZero General model-based reinforcement learning
  workflows, game/config customization, network and MCTS debugging, training
  CLI/API use, and checkpoint diagnostics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# MuZero General

Use this repo skill when a task involves MuZero General, a bundled source-snapshot implementation of DeepMind-style MuZero with PyTorch networks, Ray self-play/training workers, built-in Gym/board/card games, checkpointed results, TensorBoard logging, and optional diagnostics. The skill includes the required MuZero General source under `runtime/source/`, so core workflows and smoke helpers do not require an external checkout.

## Start here

1. Read [self-contained-runtime.md](references/self-contained-runtime.md) for bundled `runtime/source/`, default helper behavior, and editable staging.
2. Read [repo-provenance.md](references/repo-provenance.md) when checking whether the bundled source snapshot is current or before refreshing it.
3. Read [architecture-overview.md](references/architecture-overview.md) for the roles of `runtime/source/muzero.py`, game modules, networks, MCTS, replay buffer, trainer, shared storage, and diagnostics.
4. Read [troubleshooting.md](references/troubleshooting.md) for install/import, Gym/Ray, optional dependency, CPU/GPU, and bundled-source packaging issues.
5. Run the shared checker before deeper work. Omit `--repo-root` to use the bundled source snapshot:

   ```bash
   python scripts/check_muzero_environment.py --smoke --json
   ```

## Route by task

| User task | Read next | Why |
| --- | --- | --- |
| Run the self-contained MuZero entry point, build a JSON config override, start/stop training, test a model, use TensorBoard, or run HPO | [training-and-cli](sub-skills/training-and-cli/SKILL.md) | Owns bundled-source CLI/API patterns, Ray worker lifecycle, safe training smokes, expensive CI recipe, and runtime failures. |
| Choose a built-in game, add a custom game, validate `MuZeroConfig`, fix observation/action/player errors, or handle optional game packages | [games-and-configs](sub-skills/games-and-configs/SKILL.md) | Owns the `AbstractGame`/`Game` contract, built-in game catalog, config field groups, and optional dependencies. |
| Debug FC/ResNet construction, tensor shapes, support transforms, `GameHistory`, legal action masks, or MCTS behavior | [models-and-mcts](sub-skills/models-and-mcts/SKILL.md) | Owns `models.py` and `self_play.py` model/search internals and safe tensor smoke checks. |
| Load/inspect `model.checkpoint`, resume from `replay_buffer.pkl`, diagnose learned model dynamics, or avoid plotting/headless failures | [checkpoints-and-diagnostics](sub-skills/checkpoints-and-diagnostics/SKILL.md) | Owns checkpoint schema, `load_model`, `SharedStorage.save_checkpoint`, `DiagnoseModel`, and non-interactive inspection. |

## Installation and import context

MuZero General has no upstream packaging metadata, so this skill bundles the required source snapshot at `runtime/source/` and provides skill-owned entry points that add that source to `sys.path` automatically. Use an external `--repo-root` only when intentionally validating a staged editable copy or another target checkout; it is not required for core skill workflows.

Bundled-source dependency install from the skill root:

```bash
pip install -r runtime/source/requirements.lock
```

Practical modern CPU inspection often needs compatible versions of `torch`, `ray`, `gym`, `tensorboard`, `nevergrad`, `seaborn`, `matplotlib`, `numpy`, and `pygame` for classic-control environments. Optional game integrations require extra packages; do not install all optional packages unless the selected workflow needs them.

Minimal self-contained import check:

```bash
python scripts/check_muzero_environment.py --json
```

## Safe operating defaults

- Start with CPU-safe smoke checks before training: `training_steps=0`, `num_simulations=1`, `max_moves=1`, `save_model=false`, `max_num_gpus=0`, and all GPU flags false.
- Avoid the interactive no-argument CLI and game `render()` methods in unattended work.
- Treat Atari, LunarLander/Box2D, MiniGrid, OpenSpiel, Graphviz plotting, and long CartPole CI training as optional or expensive unless the user explicitly selects them.
- Use bundled scripts and `runtime/source/` instead of relying on an external source checkout, examples, or notebooks. The scripts use the bundled source by default and accept `--repo-root` only as an optional override for staged copies or user target checkouts.
- Do not claim a checkpoint is compatible with a game/config until weight shapes and key config fields are checked.

## Important bundled helpers

- `scripts/check_muzero_environment.py`: shared dependency/import/optional-game checker with an optional CPU smoke; defaults to `runtime/source/`.
- `scripts/run_muzero.py`: self-contained constructor/train/test entry point backed by `runtime/source/`.
- `scripts/stage_muzero_source.py`: copies `runtime/source/` into an editable working directory for custom games or experiments.
- `sub-skills/training-and-cli/scripts/muzero_cli_smoke.py`: safe `MuZero` constructor and optional tiny training wrapper; defaults to `runtime/source/`.
- `sub-skills/games-and-configs/scripts/list_builtin_games.py`: built-in game/dependency summary.
- `sub-skills/games-and-configs/scripts/validate_game_module.py`: custom or built-in game contract validator.
- `sub-skills/models-and-mcts/scripts/model_mcts_smoke.py`: FC/ResNet/MCTS tensor smoke.
- `sub-skills/checkpoints-and-diagnostics/scripts/inspect_checkpoint.py`: CPU-safe checkpoint/replay metadata inspector.

## Non-goals

This skill does not provide a new MuZero algorithm implementation beyond the bundled upstream source snapshot, guarantee benchmark-level training results, install optional system packages without approval, download Atari ROMs/assets, or execute long experiments by default. It prepares future agents to use and troubleshoot MuZero General workflows safely and accurately without requiring the production source checkout.
