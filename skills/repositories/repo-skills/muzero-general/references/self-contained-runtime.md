# Self-Contained Runtime Source

## Purpose

This skill does not depend on the production MuZero General checkout remaining available. It bundles the required upstream source snapshot under `runtime/source/` and provides skill-owned helpers and entry points that use that snapshot by default.

## Bundled layout

```text
runtime/source/
  BUNDLED-SOURCE-MANIFEST.json
  muzero.py
  models.py
  self_play.py
  trainer.py
  replay_buffer.py
  shared_storage.py
  diagnose_model.py
  games/*.py
  requirements.txt
  requirements.lock
  README.md
  docs/README.md
  .github/workflows/ci-testing.yaml
```

The manifest records the upstream commit and SHA-256 hash for each bundled source file. Large checkpoints, image assets, generated caches, git metadata, and review/test artifacts are intentionally not bundled as runtime source.

## Default execution model

All skill-owned helpers that need MuZero General source code use `runtime/source/` when `--repo-root` is omitted:

```bash
python scripts/check_muzero_environment.py --smoke --json
python scripts/run_muzero.py --game tictactoe --safe-smoke --mode construct --json
python sub-skills/training-and-cli/scripts/muzero_cli_smoke.py --game tictactoe --training-steps 0 --json
python sub-skills/games-and-configs/scripts/list_builtin_games.py --format table
python sub-skills/games-and-configs/scripts/validate_game_module.py --module games.tictactoe --json
python sub-skills/models-and-mcts/scripts/model_mcts_smoke.py --case both --num-simulations 1 --json
```

Use `--repo-root` only when intentionally validating a staged editable copy or another target checkout. It is not a prerequisite for core workflows.

## Installing dependencies

From the skill root, install the bundled source's dependency lock if the environment is not already prepared:

```bash
pip install -r runtime/source/requirements.lock
```

On modern Python, historical pins may need compatibility adjustments. The verified CPU scope used compatible modern versions of PyTorch, Ray, Gym, TensorBoard, Nevergrad, Seaborn, Matplotlib, NumPy, and Pygame. Optional game dependencies remain opt-in.

## Running MuZero without the upstream checkout

Use `scripts/run_muzero.py` instead of direct `runtime/source/muzero.py` invocation. The wrapper adds the bundled source to `sys.path`, has no interactive menu mode, and keeps train-mode results out of the runtime source unless an explicit path is provided.

Constructor smoke:

```bash
python scripts/run_muzero.py --game cartpole --mode construct --safe-smoke --json
```

Bounded training example:

```bash
python scripts/run_muzero.py \
  --game cartpole \
  --mode train \
  --config-json '{"training_steps": 100, "num_simulations": 5, "max_num_gpus": 0, "train_on_gpu": false, "selfplay_on_gpu": false, "reanalyse_on_gpu": false}' \
  --results-path ./muzero-results/cartpole-demo
```

## Creating editable source for custom games

Do not edit `runtime/source/` directly during user experiments. Stage a copy first:

```bash
python scripts/stage_muzero_source.py --dest <workdir>/muzero-general-source
```

Then add or modify `games/<name>.py` inside the staged copy and pass it to helpers only for that custom workflow:

```bash
python sub-skills/games-and-configs/scripts/validate_game_module.py --repo-root <workdir>/muzero-general-source --module games.<name> --json
python sub-skills/models-and-mcts/scripts/model_mcts_smoke.py --repo-root <workdir>/muzero-general-source --case custom --game-module games.<name> --num-simulations 1 --json
```

## Refresh rule

If upstream MuZero General source files, game modules, requirements, CLI/API behavior, or checkpoint schema change, refresh the skill and rebuild `runtime/source/BUNDLED-SOURCE-MANIFEST.json`. Do not patch the manifest by hand without copying the corresponding source files.
