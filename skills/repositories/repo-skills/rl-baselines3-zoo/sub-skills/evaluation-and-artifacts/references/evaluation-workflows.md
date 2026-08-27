# Evaluation workflows

This reference covers local evaluation and artifact-aware command planning for an installed RL Baselines3 Zoo package. It assumes model files already exist. If they do not, create them through the `training-cli` sub-skill instead of starting training from this sub-skill.

## Command entry points

Preferred module form:

```bash
python -m rl_zoo3.enjoy --algo ppo --env CartPole-v1 -f logs --exp-id 0 --no-render -n 1000
```

Console-subcommand form:

```bash
rl_zoo3 enjoy --algo ppo --env CartPole-v1 -f logs --exp-id 0 --no-render -n 1000
```

Use the module form when the console wrapper is unavailable or optional plotting imports make the top-level console path fragile. Both forms expose the same enjoy arguments.

## Safe no-render evaluation recipe

1. Inspect the artifact tree first:

   ```bash
   python scripts/model_artifact_inspector.py \
     --folder logs --algo ppo --env CartPole-v1 --exp-id 0
   ```

2. Run a short no-render evaluation:

   ```bash
   python -m rl_zoo3.enjoy \
     --algo ppo --env CartPole-v1 \
     -f logs --exp-id 0 \
     --no-render -n 1000 --seed 0 --verbose 1
   ```

3. If the environment needs constructor overrides, pass them as `key:python_literal` values:

   ```bash
   python -m rl_zoo3.enjoy \
     --algo ppo --env MountainCar-v0 -f logs --exp-id 1 \
     --no-render --env-kwargs goal_velocity:10
   ```

   Saved `args.yml` values override config-file `env_kwargs`; explicit `--env-kwargs` override both.

## Model selector semantics

RL Zoo resolves a run folder and then chooses a model file inside that folder.

### Run folder selection

| Argument | Effective run folder |
| --- | --- |
| `--exp-id 0` | Latest numeric run under `<folder>/<algo>/<env>_<id>`; this is the default. |
| `--exp-id N` with `N > 0` | Exact `<folder>/<algo>/<env>_N`. |
| `--exp-id -1` | No experiment subfolder: `<folder>/<algo>`. This layout is uncommon for newly trained Zoo runs but may exist for hand-arranged models. |

`--exp-id 0` looks for the greatest numeric suffix. If no matching numeric run exists, it falls back to the no-experiment layout and may then report a missing model at `<folder>/<algo>/<env>.zip`.

### Model file selection inside the run folder

| Selector | File used | Typical prerequisite |
| --- | --- | --- |
| no selector | `<env>.zip` | Final model saved at the end of training. |
| `--load-best` | `best_model.zip` | Training used evaluation callbacks, usually via a positive eval frequency. |
| `--load-checkpoint STEPS` | `rl_model_<STEPS>_steps.zip` | Training used a save/checkpoint frequency and produced that step number. |
| `--load-last-checkpoint` | Highest numeric `rl_model_*_steps.zip` | At least one checkpoint file exists; chosen by step count, not by modification time. |

Examples:

```bash
# Final model from latest numeric run
python -m rl_zoo3.enjoy --algo a2c --env Pendulum-v1 -f logs --exp-id 0 --no-render

# Best model from explicit run 1
python -m rl_zoo3.enjoy --algo a2c --env Pendulum-v1 -f logs --exp-id 1 --load-best --no-render

# Specific checkpoint
python -m rl_zoo3.enjoy --algo a2c --env Pendulum-v1 -f logs --exp-id 1 --load-checkpoint 500 --no-render

# Latest checkpoint by step count
python -m rl_zoo3.enjoy --algo a2c --env Pendulum-v1 -f logs --exp-id 1 --load-last-checkpoint --no-render
```

## Deterministic and stochastic action defaults

`enjoy` computes a final `deterministic` flag before calling the model policy:

- For most environments, actions are deterministic by default.
- Atari and MiniGrid environments are stochastic by default unless `--deterministic` is passed.
- `--stochastic` forces stochastic actions.
- For reproducible local smoke tests, pass `--deterministic --seed <int>` unless the benchmark intentionally wants the source default.

## VecNormalize and saved configuration

Evaluation creates a test environment from the saved run metadata:

1. It reads hyperparameters from `<run>/<env>/config.yml` when available.
2. It reads saved CLI arguments from `<run>/<env>/args.yml` when available, especially `env_kwargs`.
3. If normalization is enabled, it expects `<run>/<env>/vecnormalize.pkl`; missing stats raise an evaluation error.
4. `--norm-reward` only changes reward normalization behavior during evaluation; it does not create missing normalization statistics.

If a model was trained with wrappers, frame stacking, normalization, or custom environment kwargs, missing config files can make an otherwise present `.zip` fail or behave differently.

## Reward logging during evaluation

Use `--reward-log <dir>` to write evaluation Monitor output while enjoying a model:

```bash
python -m rl_zoo3.enjoy \
  --algo ppo --env CartPole-v1 -f logs --exp-id 1 \
  --no-render -n 5000 --reward-log eval-rewards/cartpole
```

This logs evaluation rewards; it does not train or update model weights. Prefer a fresh output directory per evaluation to avoid mixing runs.

## Local benchmark smoke

`python -m rl_zoo3.benchmark` enumerates trained models, calls enjoy internally with `--no-render`, writes per-model reward logs, and emits a benchmark Markdown table.

Safe offline smoke shape:

```bash
python -m rl_zoo3.benchmark \
  --log-dir logs \
  --benchmark-dir logs/benchmark \
  --test-mode --no-hub \
  -n 100 --num-threads 2
```

Important relationship:

- `--test-mode` stops after the first benchmarkable model; it does not disable Hub queries.
- `--no-hub` disables Hub model enumeration/download. Use it for offline, credential-free, or deterministic local tests.
- If the default `rl-trained-agents/` folder is absent, point `--log-dir` to a local log tree that actually contains Zoo-style model folders.
- Benchmark result interpretation and plotting belong to the `plotting-benchmarking` sub-skill.

## Progress bars and optional dependencies

`-P`/`--progress` uses `tqdm` and `rich`. If those packages are absent, omit progress for evaluation smoke tests; it does not affect model loading semantics.

## Off-policy model loading note

For off-policy algorithms such as DQN, QRDQN, DDPG, SAC, TD3, TQC, and HER, evaluation loads the model with a dummy `buffer_size=1` because replay memory is not needed for enjoying a trained agent. This is expected and does not mean the original replay buffer is present.
