# Optuna tuning workflow

This reference covers RL Zoo hyperparameter optimization (HPO) only. For ordinary training flags and safe timestep budgets, route to [`../../training-cli/SKILL.md`](../../training-cli/SKILL.md). For YAML/Python config and `-params` syntax, route to [`../../config-hyperparams/SKILL.md`](../../config-hyperparams/SKILL.md). For plotting outputs, route to [`../../plotting-benchmarking/SKILL.md`](../../plotting-benchmarking/SKILL.md).

## Supported HPO algorithms

The HPO search space is defined by RL Zoo's sampler/converter maps. Current supported HPO algorithm ids are:

`a2c`, `ars`, `ddpg`, `dqn`, `ppo`, `ppo_lstm`, `qrdqn`, `sac`, `td3`, `tqc`, `trpo`.

The general train CLI may expose additional algorithm ids. Do not build `--optimize-hyperparameters` commands for an algorithm that has no sampler/converter entry unless the package has been extended with a matching HPO search space.

## Command patterns

Prefer module invocation for the broadest installed-package compatibility:

```bash
python -m rl_zoo3.train --algo ppo --env MountainCar-v0 -n 50000 \
  --optimize-hyperparameters --n-trials 1000 --n-jobs 2 \
  --sampler tpe --pruner median --n-evaluations 2 --no-optim-plots
```

Use shared storage and a stable study name when multiple workers or later trial reuse matter:

```bash
python -m rl_zoo3.train --algo ppo --env MountainCar-v0 -n 50000 \
  --optimize-hyperparameters --storage sqlite:///runs/optuna/rlzoo.db \
  --study-name mountaincar-ppo --max-total-trials 300 --n-jobs 4 \
  --sampler tpe --pruner median --optimization-log-path runs/optuna/trial-logs \
  --no-optim-plots
```

Load one stored trial and train with its converted hyperparameters; this is not a new HPO run:

```bash
python -m rl_zoo3.train --algo ppo --env MountainCar-v0 -n 50000 \
  --storage sqlite:///runs/optuna/rlzoo.db --study-name mountaincar-ppo --trial-id 21
```

`rl_zoo3 train ...` is also a valid installed-package launcher when the console entry point and optional plotting import path are available. See [`../../../references/install-and-environment.md`](../../../references/install-and-environment.md) for that boundary.

## HPO lifecycle

1. RL Zoo loads base hyperparameters from the selected config source and CLI overrides.
2. If `--storage`, `--study-name`, and `--trial-id` are all present, it loads the stored trial parameters and converts them back to train-ready hyperparameters before ordinary training.
3. For a new HPO run, `--optimize-hyperparameters` creates the configured sampler and pruner, then creates or reuses an Optuna study.
4. Each trial samples algorithm-specific hyperparameters, merges them into the base config, creates train/eval environments, trains for the requested timestep budget, and reports intermediate rewards through the trial-evaluation callback.
5. Invalid sampled hyperparameters that raise assertion/value errors, including NaN-producing combinations, are pruned rather than treated as successful trials.
6. If `--optimization-log-path` is set, each trial writes evaluation artifacts under a `trial_<trial.number>/` folder.
7. After optimization, RL Zoo writes a study report CSV and pickle under the algorithm log folder. Optional Optuna plots are attempted unless `--no-optim-plots` is passed.

## HPO flag semantics

| Flag | Meaning | Operating note |
| --- | --- | --- |
| `-optimize`, `--optimize-hyperparameters` | Switch from ordinary training to Optuna search. | Do not combine with a `--trial-id` replay command. |
| `--n-trials` | Number of trials for each optimization runner. | Per-worker budget; defaults are large enough to be expensive. |
| `--max-total-trials` | Total cap for complete, running, or pruned trials across the study. | Takes precedence over `--n-trials`; use shared `--storage` and `--study-name` for distributed workers. |
| `--n-jobs` | Parallel jobs inside one optimization runner. | Must be greater than 1 when `--pruner halving` is used. |
| `--sampler random` | Random search. | Useful for quick smoke checks and broad baselines. |
| `--sampler tpe` | Tree-structured Parzen Estimator sampler. | Uses `--n-startup-trials` before model-based sampling. |
| `--sampler auto` | OptunaHub auto sampler. | Requires the optional `optunahub` package at runtime. |
| `--pruner halving` | Successive halving pruner. | Requires `--n-jobs > 1`. |
| `--pruner median` | Median pruner. | Uses `--n-startup-trials` and a warmup based on `--n-evaluations`. |
| `--pruner none` | Disable pruning. | Safer for debugging but more expensive. |
| `--n-startup-trials` | Warmup trials before sampler/pruner decisions. | Especially relevant for TPE and median pruning. |
| `--n-evaluations` | Intermediate evaluations per trial. | Evaluation frequency is computed from `n_timesteps / n_evaluations`, then adjusted for vectorized environments. |
| `--storage` | Optuna storage URI or journal `.log` path. | `.log` storage is treated as Optuna journal storage; SQL URIs such as `sqlite:///...` can be shared. |
| `--study-name` | Reusable Optuna study identifier. | Required for reliable distributed optimization and later `--trial-id` reuse. |
| `--trial-id` | Load one stored trial into a normal train run. | Requires both `--storage` and `--study-name`; trial params are converted before merging into training hyperparameters. |
| `--optimization-log-path` | Per-trial evaluation and best-policy artifacts. | Separate from the final `report_*.csv` / `report_*.pkl` study reports. |
| `--no-optim-plots` | Skip post-optimization interactive plots. | Does not disable CSV/pickle report writing; recommended for headless or unattended runs. |

## Search-space notes

- The sampler map defines what can be tuned; hyperparameters absent from the HPO sampler come from the selected RL Zoo config and then the underlying algorithm defaults.
- The converter map rehydrates sampled Optuna parameters into real training parameters. Examples: `one_minus_gamma` becomes `gamma`; power-of-two exponents become integer `n_steps` or `batch_size`; categorical network names become policy architecture dictionaries/lists.
- On-policy families (`a2c`, `ppo`, `ppo_lstm`, `trpo`) tune learning-rate, discount/GAE terms, network architecture, activation function, and algorithm-specific values such as PPO clip/n-epoch values or TRPO conjugate-gradient/target-KL settings.
- Off-policy families (`ddpg`, `td3`, `sac`, `dqn`, `qrdqn`, `tqc`) tune discount, learning rate, batch size, training frequency, architecture, and family-specific noise, quantile, or HER replay-buffer parameters. For TD3/DDPG-style tuning, gradient steps are coupled to train frequency to reduce the search space.
- `ars` tunes ARS-specific perturbation and selection parameters such as delta count/scale, learning rate, and top-fraction size.
- Some tuning defaults intentionally differ from raw Stable-Baselines3 defaults. Treat the HPO search space as its own operating mode, not just ordinary training with random CLI overrides.
