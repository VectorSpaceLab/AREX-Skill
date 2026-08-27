# Optuna study artifacts

RL Zoo HPO produces two artifact families: final study reports under the normal algorithm log folder and optional per-trial evaluation folders under `--optimization-log-path`.

## Final study reports

After an optimization run finishes or is interrupted cleanly, RL Zoo writes both report files under the selected log folder and algorithm id:

```text
<log-folder>/<algo>/report_<env>_<n-trials>-trials-<n-timesteps>-<sampler>-<pruner>_<timestamp>.csv
<log-folder>/<algo>/report_<env>_<n-trials>-trials-<n-timesteps>-<sampler>-<pruner>_<timestamp>.pkl
```

- The CSV is produced from the Optuna trials dataframe and is the fastest artifact for tabular review.
- The pickle contains the Optuna `Study` object and can be used for study-level inspection in a compatible Python/Optuna environment.
- These reports are written even when `--no-optim-plots` is set; that flag only skips optional plot display.
- The report name includes the per-runner `--n-trials` value even when `--max-total-trials` is the real global stop condition.

## Per-trial optimization logs

If `--optimization-log-path <path>` is supplied, each trial gets a folder named with the Optuna trial number:

```text
<optimization-log-path>/trial_<trial.number>/
  evaluations.npz
  best_model.zip          # when the evaluation callback saves a best policy
```

Use this folder when a task asks which candidate trial had an evaluation trace or when a later plotting/benchmarking task needs evaluation files. For visualization workflows, route to [`../../plotting-benchmarking/SKILL.md`](../../plotting-benchmarking/SKILL.md).

## Storage-backed studies

`--storage` controls reusable Optuna state:

- A path ending in `.log` is treated as Optuna journal storage.
- A URI such as `sqlite:///runs/optuna/rlzoo.db` is passed to Optuna as database-backed storage.
- Use the same `--storage` and `--study-name` for every worker that should contribute to the same study.
- If `--storage` is provided without `--study-name`, Optuna can create a generated study name, but future workers or replay commands may not know what name to reuse.

## Reusing a trial

A replay command with `--storage`, `--study-name`, and `--trial-id` is ordinary training initialized from study parameters; it is not a fresh HPO search.

Behavior to remember:

1. The selected study is loaded from the storage backend.
2. `--trial-id N` selects the stored trial at that trial number/index.
3. The lower-level trial loader can default to the best trial when called without an id, but the train CLI study-loading path is triggered only when `--storage`, `--study-name`, and `--trial-id` are all present.
4. Trial parameters are converted through the algorithm-specific converter before they are merged into train hyperparameters.
5. CLI `-params` overrides, if supplied, still update the resulting hyperparameters after the study parameters are loaded.

## Deprecated parse-study flow

The old source-distribution `parse_study.py` helper is deprecated. It can load a saved study pickle or storage-backed study, sort trials by value, print top-trial parameters, and save JSON files such as `hyperparameters_1.json`. Treat it as legacy evidence only. For new workflows, prefer one of these paths:

- Use `--storage` + `--study-name` + `--trial-id` to replay a chosen trial.
- Use the report CSV for tabular inspection.
- Use a compatible Optuna study viewer against the storage backend when live inspection is needed.
