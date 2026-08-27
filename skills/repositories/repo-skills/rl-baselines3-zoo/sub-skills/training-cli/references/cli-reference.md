# Training CLI reference

## Entry points

| Form | Use when | Notes |
| --- | --- | --- |
| `python -m rl_zoo3.train ...` | Preferred training entry point | Works from any directory where `rl_zoo3` is installed and avoids console-router plotting imports. |
| `rl_zoo3 train ...` | Console entry point is installed and imports cleanly | Equivalent command surface for training; may require plotting extras because the router imports plot modules. |

The checkout-local `python train.py ...` shim is equivalent to calling the package training function, but operating commands should prefer the installed-package forms above.

## Algorithms from the RL Zoo registry

`--algo` accepts:

```text
a2c, ddpg, dqn, ppo, sac, td3, ars, crossq, qrdqn, tqc, trpo, ppo_lstm
```

Practical environment pairings for fast checks:

- Discrete/classic-control smoke: `ppo`, `a2c`, `dqn`, `qrdqn`, `trpo`, `ars` with `CartPole-v1` when compatible.
- Continuous-control smoke: `sac`, `td3`, `ddpg`, `tqc`, `crossq` with `Pendulum-v1`.
- Optional simulator families such as Atari, MuJoCo, Box2D, PyBullet, highway, Minigrid, and robotics require their own packages/data and are not assumed by this sub-skill.

## Core training flags

| Flag | Meaning | Operating notes |
| --- | --- | --- |
| `--algo {…}` | Select RL algorithm | Must be one of the registry ids listed above. |
| `--env ENV_ID` | Gymnasium environment id | RL Zoo imports `--gym-packages` first, then checks the Gymnasium registry and raises a closest-match error on failure. |
| `-n`, `--n-timesteps INT` | Override configured timesteps | Strongly recommended for smoke or bounded runs; if omitted, config defaults may be very large. |
| `-f`, `--log-folder PATH` | Root output folder | Output goes under `PATH/algo/env_id_runid[_uuid]`. Use a task-specific folder. |
| `--seed INT` | Random seed | Negative or omitted seed is replaced by a random seed. Use a nonnegative seed for reproducibility. |
| `--num-threads INT` | PyTorch thread count | `-1` leaves default; positive values call `torch.set_num_threads`. CPU runs often use `1` or a small value. |
| `--device DEVICE` | PyTorch device | `auto` is default. Use `cpu` for portability; use `cuda` only when available. |
| `--verbose INT` | Verbosity | `0` quiet, `1` info. |
| `--log-interval INT` | Stable-Baselines3 logging interval | `-1` keeps default; values below `-1` pass `log_interval=None` to suppress automatic logging. |
| `--progress`, `-P` | Show progress bar | Adds a progress-bar callback. Omit in noisy/non-interactive logs if needed. |

## Logging, evaluation, and checkpoints

| Flag | Meaning | Operating notes |
| --- | --- | --- |
| `--tensorboard-log PATH` / `-tb PATH` | TensorBoard root | RL Zoo appends the environment name to this root unless W&B tracking rewrites it. |
| `--eval-freq INT` | Evaluation interval | `>0` creates an evaluation callback; negative disables evaluation. Positive values are divided by `n_envs`. |
| `--eval-episodes INT` | Evaluation episodes | Default is 5. Use low values for smoke tests, higher values for reporting. |
| `--n-eval-envs INT` | Number of eval envs | Default is 1. Eval envs use `--eval-env-kwargs` when supplied. |
| `--save-freq INT` | Checkpoint interval | `>0` creates `rl_model_<steps>_steps.zip`; negative disables checkpoints. Positive values are divided by `n_envs`. |
| `--save-replay-buffer` | Save replay buffer | Meaningful only for algorithms/models that implement replay buffers. Saves `replay_buffer.pkl` in the run folder. |
| `--uuid`, `-uuid` | Unique run suffix | Appends a UUID to the run folder, useful for concurrent launches. |

Evaluation callback outputs include `best_model.zip` and `evaluations.npz` under the run folder. Checkpoint callback outputs `rl_model_<steps>_steps.zip` under the same run folder.

## Continuation and replay buffer flags

| Flag | Meaning | Operating notes |
| --- | --- | --- |
| `--trained-agent PATH`, `-i PATH` | Continue training from a saved zip | Path must exist and end in `.zip`; RL Zoo asserts this before creating the manager. |
| `--truncate-last-trajectory BOOL` | HER replay-buffer reload behavior | Default is true. Because the parser uses Python `bool` conversion, omit the flag unless you have verified the desired runtime parsing. |
| `--save-replay-buffer` | Save buffer after this run | Also pairs with continuation: if `replay_buffer.pkl` is adjacent to `--trained-agent`, RL Zoo loads it automatically before learning. |

Continuation removes current `policy` and `policy_kwargs` from loaded hyperparameters before loading the saved model so the zip's policy remains consistent.

## Environment and vectorization flags

| Flag | Meaning | Operating notes |
| --- | --- | --- |
| `--gym-packages MOD [MOD ...]` | Import custom registration modules | Use for external/custom envs. Every module must be importable in the current Python environment and in subprocess workers if using `--vec-env subproc`. |
| `--env-kwargs KEY:EXPR [KEY:EXPR ...]` | Constructor kwargs for training env | Values are evaluated as Python expressions by RL Zoo. Quote shell-sensitive values. |
| `--eval-env-kwargs KEY:EXPR [KEY:EXPR ...]` | Constructor kwargs for eval env | If omitted, RL Zoo uses training `env_kwargs` for eval too. |
| `--vec-env {dummy,subproc}` | Vectorized env implementation | `dummy` is default and memory-light; `subproc` may help expensive envs but adds pickling/import constraints. |

The number of training envs is not a standalone train CLI flag. It comes from config or CLI hyperparameter override, commonly `--hyperparams n_envs:4`.

## Config and hyperparameter override flags

| Flag | Meaning | Route |
| --- | --- | --- |
| `--conf-file PATH_OR_MODULE`, `-conf PATH_OR_MODULE` | Load YAML, Python file, or Python module containing `hyperparams` | Use `../../config-hyperparams/SKILL.md` for grammar and validation. |
| `--hyperparams KEY:EXPR [KEY:EXPR ...]`, `-params ...` | Override config values on CLI | Use `../../config-hyperparams/SKILL.md` for safe expression grammar, wrappers, callbacks, schedules, and quoting. |

Examples that remain in this sub-skill because they affect training operations:

```bash
python -m rl_zoo3.train --algo ppo --env CartPole-v1 \
  --n-timesteps 1000 --hyperparams n_envs:2 n_steps:64
```

```bash
python -m rl_zoo3.train --algo sac --env Pendulum-v1 \
  --n-timesteps 1000 --hyperparams buffer_size:1000 \
  --env-kwargs g:8.0 --eval-env-kwargs g:5.0
```

## Routed flags from the shared train parser

The train parser also accepts these flags, but this sub-skill only routes them:

| Flag group | Flags | Route |
| --- | --- | --- |
| Optuna optimization | `--optimize-hyperparameters`, `-optimize`, `--n-trials`, `--max-total-trials`, `--n-jobs`, `--sampler`, `--pruner`, `--n-startup-trials`, `--n-evaluations`, `--storage`, `--study-name`, `--trial-id`, `--optimization-log-path`, `--no-optim-plots` | `../../tuning-optimization/SKILL.md` |
| Weights & Biases | `--track`, `--wandb-project-name`, `--wandb-entity`, `--wandb-group`, `--wandb-tags`, `-tags` | `../../integrations-hub-tracking/SKILL.md` |

Do not treat HPO as a normal training run: it creates Optuna studies/reports and changes evaluation behavior. Do not treat W&B tracking as local-only: it may require the `wandb` package, credentials, and network access.

## Builder helper examples

Module command, bounded CPU smoke:

```bash
python ../scripts/train_command_builder.py --algo ppo --env CartPole-v1 \
  --n-timesteps 1000 --log-folder ./runs/smoke \
  --eval-freq 500 --save-freq 500 --seed 123 --device cpu
```

Console command, with warning about console-router imports:

```bash
python ../scripts/train_command_builder.py --command-style console \
  --algo ppo --env CartPole-v1 --n-timesteps 1000 --log-folder ./runs/smoke
```

Off-policy continuation command plan when files will exist at runtime:

```bash
python ../scripts/train_command_builder.py --algo sac --env Pendulum-v1 \
  --n-timesteps 1000 --log-folder ./runs/sac-buffer \
  --trained-agent ./runs/sac-buffer/sac/Pendulum-v1_1/Pendulum-v1.zip \
  --allow-missing-files --save-replay-buffer --expect-replay-buffer \
  --hyperparams buffer_size:1000 --env-kwargs g:8.0 --eval-env-kwargs g:5.0
```
