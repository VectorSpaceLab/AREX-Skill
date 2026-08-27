---
name: training-and-cli
description: "Runs and troubleshoots MuZero General CLI, Python API, Ray
  training/testing, TensorBoard logging, and safe smoke workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Training and CLI

Use this sub-skill when the task is to run MuZero General, build a safe training or testing command, use the `MuZero` Python API, adjust a JSON config override, understand Ray workers, inspect the upstream CartPole CI recipe, or debug training/runtime startup failures.

## Fast route

1. Read [training-workflows.md](references/training-workflows.md) for self-contained bundled-source entry points, Python API patterns, TensorBoard usage, hyperparameter search, and safe smoke overrides.
2. Read [api-reference.md](references/api-reference.md) when you need verified signatures, constructor behavior, worker roles, checkpoint lifecycle, or replay/trainer/shared-storage interactions.
3. Read [troubleshooting.md](references/troubleshooting.md) for invalid game/config names, Ray startup failures, GPU resource conflicts, long-running training, TensorBoard confusion, Gym/Ray warnings, or interactive menu blocking.
4. Run the bundled safe smoke helper before real training:

   ```bash
   python sub-skills/training-and-cli/scripts/muzero_cli_smoke.py --game tictactoe --training-steps 0 --json
   ```

   The helper imports the bundled `runtime/source/` snapshot by default, constructs `MuZero`, applies CPU-safe overrides, reports key config/checkpoint facts, and shuts Ray down. It does not train unless `--run-train` is explicitly supplied. Use `--repo-root` only for a staged editable copy or another target checkout.

## Primary workflows

- **Self-contained entry point:** from the skill root, use `python scripts/run_muzero.py --game <game> --config-json '<json-config>' --mode construct|train|test`. It runs against bundled `runtime/source/` unless `--repo-root` points to an intentionally staged copy or target checkout. Use JSON overrides for bounded runs such as `{"training_steps": 0, "num_simulations": 1, "max_moves": 1, "save_model": false}`.
- **Python API run:** instantiate `MuZero(game_name, config=None, split_resources_in=1)`, optionally call `load_model(...)`, then call `train(log_in_tensorboard=True|False)` or `test(render=False, ...)`.
- **Smoke before training:** prefer the bundled helper or `python scripts/run_muzero.py --game tictactoe --safe-smoke --mode construct --json` before launching Ray workers that can run indefinitely.
- **Real training:** choose a game/config in sibling [games-and-configs](../games-and-configs/SKILL.md), validate model/search shapes in [models-and-mcts](../models-and-mcts/SKILL.md), then run training with a deliberate result path and TensorBoard plan.
- **Checkpoint-aware runs:** read [checkpoints-and-diagnostics](../checkpoints-and-diagnostics/SKILL.md) before loading `model.checkpoint` or `replay_buffer.pkl` artifacts.

## Safety boundaries

- Do not run the upstream interactive menu (`runtime/source/muzero.py` with no args) in automation unless the user explicitly wants prompts. Prefer `scripts/run_muzero.py`, which has no interactive menu mode.
- Do not run the upstream 7,500-step CartPole CI recipe as a normal smoke; it is an expensive native candidate, not the default verification path.
- Do not enable `train_on_gpu`, `selfplay_on_gpu`, or `reanalyse_on_gpu` while setting `max_num_gpus = 0`.
- Do not assume all optional games are installed. Atari, LunarLander/Box2D, MiniGrid, and OpenSpiel need extra packages; route those checks to [games-and-configs](../games-and-configs/SKILL.md).

## When to stop and ask

Ask for user approval before long training, installing optional game dependencies, downloading Atari ROM/assets, using GPUs for a heavy run, or overwriting/checkpointing into a user-important results directory. Otherwise use bounded CPU-safe smoke checks first.
