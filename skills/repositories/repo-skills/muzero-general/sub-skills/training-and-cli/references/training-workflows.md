# Training Workflows

## Purpose

Read this for MuZero General CLI/API run patterns, safe smoke overrides, Ray worker lifecycle, TensorBoard logging, hyperparameter search, and the upstream CartPole CI recipe. It distills the README, `muzero.py`, `trainer.py`, `replay_buffer.py`, `shared_storage.py`, the Colab notebook, and the CI workflow.

## Self-contained command patterns

The skill bundles the required MuZero General source snapshot under `runtime/source/`. Prefer the skill-owned non-interactive entry point instead of invoking upstream `muzero.py` directly:

```bash
python scripts/run_muzero.py --game cartpole --mode construct --config-json '{"training_steps": 100, "num_simulations": 5}' --json
python scripts/run_muzero.py --game cartpole --mode train --config-json '{"training_steps": 100, "num_simulations": 5}' --results-path ./muzero-results/cartpole-demo
```

`--config-json` must decode to a JSON object. Every key is applied only if that attribute exists on the selected game's `MuZeroConfig`; otherwise the wrapper preserves MuZero General's user-facing failure: `<game> config has no attribute '<param>'. Check the config file for the complete list of parameters.`

Use safe smoke overrides before real training:

```bash
python scripts/run_muzero.py --game cartpole --mode construct --safe-smoke --json
python sub-skills/training-and-cli/scripts/muzero_cli_smoke.py --game tictactoe --training-steps 0 --json
```

Notes:

- Omit `--repo-root` for all bundled built-in workflows; helpers default to `runtime/source/`.
- Pass `--repo-root <staged-muzero-source>` only for a source copy created with `scripts/stage_muzero_source.py` or another explicit target checkout.
- With no arguments, upstream `runtime/source/muzero.py` opens an interactive menu; avoid that in automated tasks. `scripts/run_muzero.py` has no interactive menu mode.
- In train mode, `scripts/run_muzero.py` defaults `results_path` to `./muzero-results/<game>/<timestamp>` when no path is supplied, so real training does not write into the bundled runtime source by accident.
- Training can run for thousands to millions of steps by default; always inspect the chosen game config first.

## Python API pattern

```python
# When writing a custom Python script, add the bundled source snapshot first.
# The bundled helper scripts do this automatically.
import sys
from pathlib import Path
sys.path.insert(0, str(Path("runtime/source").resolve()))
from muzero import MuZero

config = {
    "training_steps": 0,
    "num_simulations": 1,
    "max_moves": 1,
    "save_model": False,
    "max_num_gpus": 0,
    "train_on_gpu": False,
    "selfplay_on_gpu": False,
    "reanalyse_on_gpu": False,
}
agent = MuZero("tictactoe", config)
# Optional before training/testing:
# agent.load_model(checkpoint_path="model.checkpoint", replay_buffer_path="replay_buffer.pkl")
# Real training only when authorized:
# agent.train(log_in_tensorboard=False)
agent.terminate_workers()
```

`MuZero.__init__` starts Ray (`ray.init(...)`) and builds initial network weights through a CPU Ray actor. Shut Ray down after scripts/tests with `ray.shutdown()` or by using the bundled smoke helper.

## Training flow inside `MuZero.train`

`train(log_in_tensorboard=True)` does the following:

1. Creates `results_path` when TensorBoard logging or `save_model` is enabled.
2. Computes per-worker GPU allocation from `self.num_gpus`, `train_on_gpu`, `selfplay_on_gpu`, `reanalyse_on_gpu`, `num_workers`, and whether logging uses a test worker.
3. Creates Ray actors:
   - `trainer.Trainer` for network weight updates.
   - `shared_storage.SharedStorage` for checkpoint/info exchange.
   - `replay_buffer.ReplayBuffer` for self-play games and batch targets.
   - optional `replay_buffer.Reanalyse` when `use_last_model_value` is true.
   - one or more `self_play.SelfPlay` workers for data generation.
4. Launches continuous self-play and continuous weight updates.
5. If `log_in_tensorboard=True`, enters `logging_loop`, starts a test worker, writes TensorBoard scalars/text, and loops until `training_step >= training_steps` or interrupted.
6. Calls `terminate_workers()` and, when saving is enabled, persists `replay_buffer.pkl`.

If `log_in_tensorboard=False`, training is launched asynchronously and the caller must decide when/how to terminate or observe workers. For bounded automation, prefer smoke helpers or explicit low `training_steps` plus polling.

## Testing flow

`MuZero.test(render=True, opponent=None, muzero_player=None, num_tests=1, num_gpus=0)` creates a `SelfPlay` worker and runs `play_game` `num_tests` times. Use `render=False` for automation; render methods often call `input("Press enter...")` and block.

Opponent handling:

- `None` uses `config.opponent`.
- `"self"` makes MuZero control every turn through MCTS.
- `"random"` samples from the current legal action list.
- `"expert"` calls the game wrapper's `expert_agent()` when implemented.
- `"human"` asks for interactive input through the game wrapper and should not be used in unattended checks.

## TensorBoard

For real training through `scripts/run_muzero.py`, choose an explicit result path and point TensorBoard there:

```bash
python scripts/run_muzero.py --game cartpole --mode train --config-json '{"training_steps": 100}' --results-path ./muzero-results/cartpole-demo --log-in-tensorboard
tensorboard --logdir ./muzero-results/cartpole-demo
```

`logging_loop` writes:

- total/muzero/opponent reward, episode length, mean root value;
- self-played games/steps, training steps, reanalysed games, training-to-self-play ratio;
- learning rate and value/reward/policy/total losses;
- hyperparameter table and model summary text.

In notebooks, the upstream source notebook uses `%tensorboard --logdir ./results` and then runs `!python muzero.py`. Treat this as human/Colab evidence only; use the bundled entry point for self-contained automation and do not execute a notebook as verification.

## Upstream CI recipe

The repo CI uses Python 3.7, installs `requirements.lock`, runs Black, then launches:

```bash
python scripts/run_muzero.py --game cartpole --mode train --config-json '{"training_steps": 7500}' --results-path ./muzero-results/cartpole-ci 2>&1 | tee log.txt
```

It parses the best reward from logs and fails when `BEST_REWARD < 250`. This is valuable native evidence but not a default smoke: it has a 90-minute job timeout and runs real training.

## Hyperparameter search

`hyperparameter_search(game_name, parametrization, budget, parallel_experiments, num_tests)` uses Nevergrad `OnePlusOne`, launches several `MuZero` experiments in parallel, trains each, tests finished experiments, tells the optimizer the negative result, and saves best weights plus `best_parameters.txt` when a best training exists.

Use it only when the user explicitly wants HPO and provides a budget. Avoid using it as a correctness check because it intentionally launches multiple training jobs.

## Safe smoke strategy

1. Validate dependency/import state with root `scripts/check_muzero_environment.py --smoke --json`.
2. Validate the selected game module with `sub-skills/games-and-configs/scripts/validate_game_module.py --module games.<name> --json`.
3. Validate model/MCTS tensor shapes with `sub-skills/models-and-mcts/scripts/model_mcts_smoke.py --case both --num-simulations 1 --json` or a custom staged-source case.
4. Run `sub-skills/training-and-cli/scripts/muzero_cli_smoke.py --game <name> --training-steps 0 --json` to verify `MuZero` constructor/Ray startup.
5. Only then run real training through `scripts/run_muzero.py --mode train`, with explicit training steps, result path policy, TensorBoard policy, and stop condition.
