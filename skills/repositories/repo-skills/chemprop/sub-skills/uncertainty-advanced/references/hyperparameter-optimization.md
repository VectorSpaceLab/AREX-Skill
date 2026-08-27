# Hyperparameter Optimization with `chemprop hpopt`

`chemprop hpopt` runs Chemprop training trials through Ray Tune, writes search outputs, and saves a best configuration that can be reused with `chemprop train --config-path`. It uses the same core data, task, split, metric, feature, transfer, and hardware flags as `chemprop train`, plus Ray Tune search controls.

## Optional Dependency Requirement

Hyperparameter optimization needs optional Ray Tune dependencies. If they are missing, ordinary Chemprop training and prediction can still work, but `chemprop hpopt` fails. Install the hpopt extra or the needed Ray/search packages in the environment that runs Chemprop.

Search algorithm extras matter:

- `--raytune-search-algorithm random`: avoids HyperOpt/Optuna-specific search package requirements.
- `--raytune-search-algorithm hyperopt`: requires HyperOpt search support; this is Chemprop's default search algorithm.
- `--raytune-search-algorithm optuna`: requires Optuna search support.

## Basic Command

```bash
chemprop hpopt \
  --data-path train.csv \
  --task-type regression \
  --search-parameter-keywords basic \
  --raytune-num-samples 10 \
  --hpopt-save-dir hpopt/regression_basic \
  --epochs 20 \
  --num-workers 0
```

After hpopt finishes, apply the best config in a training run:

```bash
chemprop train \
  --data-path train.csv \
  --task-type regression \
  --config-path hpopt/regression_basic/best_config.toml \
  --output-dir runs/regression_best
```

Command-line flags override config-file values. Keep schema, task type, feature, and split semantics consistent between hpopt and the final train command.

## Search Parameter Keywords

Common `--search-parameter-keywords` values:

| Keyword | Expands to |
| --- | --- |
| `basic` | `depth`, `ffn_num_layers`, `dropout`, `ffn_hidden_dim`, `message_hidden_dim`, plus atom/bond FFN entries only when relevant. |
| `learning_rate` | `max_lr`, `init_lr_ratio`, `final_lr_ratio`, `warmup_epochs`. |
| `all` | Every supported search parameter, subject to pruning based on task and options. |
| Individual names | Any supported parameter such as `activation`, `aggregation`, `aggregation_norm`, `batch_size`, `depth`, or `dropout`. |

Individual search parameters include:

- `activation`
- `dropout`
- `message_hidden_dim`
- `depth`
- `aggregation`
- `aggregation_norm`
- `ffn_hidden_dim`
- `ffn_num_layers`
- `atom_ffn_hidden_dim`
- `atom_ffn_num_layers`
- `atom_constrainer_ffn_hidden_dim`
- `atom_constrainer_ffn_num_layers`
- `bond_ffn_hidden_dim`
- `bond_ffn_num_layers`
- `bond_constrainer_ffn_hidden_dim`
- `bond_constrainer_ffn_num_layers`
- `batch_size`
- `init_lr_ratio`
- `max_lr`
- `final_lr_ratio`
- `warmup_epochs`

When `warmup_epochs` is searched, Chemprop requires training epochs to be at least `6` because warmup is sampled as part of the epoch schedule.

## Automatic Search-Space Pruning

Chemprop prunes requested search parameters before running trials:

- If there are no atom or bond target columns, atom/bond FFN search parameters are removed.
- If `--from-foundation` is used, message-passing architecture choices such as `activation`, `dropout`, `depth`, `aggregation`, `aggregation_norm`, and `message_hidden_dim` are removed because the message-passing layer is initialized from the foundation model.
- If no constraints path is provided, atom/bond constrainer FFN search parameters are removed.
- If `--hyperopt-n-initial-points` is omitted, Chemprop uses half of `--raytune-num-samples`.

This means the actual search space can be smaller than the keyword list in the command.

## Ray Tune Controls

Common controls:

```bash
chemprop hpopt \
  --data-path train.csv \
  --task-type regression \
  --search-parameter-keywords basic learning_rate \
  --raytune-num-samples 30 \
  --raytune-search-algorithm hyperopt \
  --raytune-trial-scheduler AsyncHyperBand \
  --raytune-grace-period 10 \
  --raytune-reduction-factor 2 \
  --raytune-num-workers 1 \
  --raytune-num-cpus 8 \
  --raytune-max-concurrent-trials 4 \
  --hpopt-save-dir hpopt/async_basic_lr
```

Flag meanings:

- `--raytune-num-samples`: number of trial configurations.
- `--raytune-search-algorithm`: `random`, `hyperopt`, or `optuna`.
- `--raytune-trial-scheduler`: `FIFO` or `AsyncHyperBand`.
- `--raytune-num-workers`: Ray workers per trial.
- `--raytune-use-gpu`: asks Ray workers to use GPU.
- `--raytune-num-cpus`, `--raytune-num-gpus`: total resources exposed to Ray.
- `--raytune-max-concurrent-trials`: maximum trial concurrency.
- `--raytune-temp-dir`: Ray temporary directory.
- `--raytune-num-checkpoints-to-keep`: checkpoint retention per trial.
- `--hyperopt-n-initial-points` and `--hyperopt-random-state-seed`: HyperOpt-specific controls.

If Ray + Lightning initialization fails for distributed execution, Chemprop can fall back to CPU/plain Lightning for the trial trainer. Treat that as a performance or environment issue, not necessarily a data/schema issue.

## Split Semantics

`hpopt` uses Chemprop training split arguments. Unlike older v1 behavior, hpopt does not automatically train on all input data; it uses train/validation/test splitting unless overridden. If `--num-replicates` is greater than one, hpopt uses only the first split for optimization. For separate optimization across several folds, run separate hpopt commands with explicit split files or split columns.

## Task-Specific Examples

### Regression MVE Search

Use hpopt to tune a future uncertainty model, then perform uncertainty prediction after final training:

```bash
chemprop hpopt \
  --data-path train.csv \
  --task-type regression-mve \
  --search-parameter-keywords basic learning_rate \
  --raytune-num-samples 20 \
  --tracking-metric val_loss \
  --hpopt-save-dir hpopt/mve

chemprop train \
  --data-path train.csv \
  --task-type regression-mve \
  --config-path hpopt/mve/best_config.toml \
  --output-dir runs/mve_best
```

### Classification Search with Explicit Metric

```bash
chemprop hpopt \
  --data-path tox.csv \
  --task-type classification \
  --metrics roc prc accuracy \
  --tracking-metric prc \
  --search-parameter-keywords basic \
  --raytune-num-samples 16 \
  --hpopt-save-dir hpopt/tox_prc
```

### Foundation Initialization Search

Foundation starts can be combined with hpopt, but message-passing architecture choices are pruned:

```bash
chemprop hpopt \
  --data-path small_task.csv \
  --task-type regression \
  --from-foundation CheMeleon \
  --search-parameter-keywords basic learning_rate \
  --raytune-num-samples 12 \
  --hpopt-save-dir hpopt/foundation_ffn_lr
```

Expect the effective search to focus on FFN, learning-rate, batch-size, or other non-foundation-pruned choices.

## Output Expectations

Typical hpopt outputs under `--hpopt-save-dir` include:

- Ray Tune result directories under `ray_results`.
- `best_config.toml` for reuse with `chemprop train --config-path`.
- `best_checkpoint.ckpt` for the best trial checkpoint.

Use `best_config.toml` for a clean final training run unless the user specifically wants the trial checkpoint.

## When Not To Use Hpopt

- Do not use hpopt just to smoke-test CSV parsing; run a short `chemprop train --epochs 1 --num-workers 0` first.
- Do not use hpopt to calibrate uncertainty; calibration is a prediction-time `chemprop predict` concern.
- Do not use hpopt if optional Ray/search dependencies are unavailable and the user cannot install them; manually choose conservative training hyperparameters through `training-cli` instead.
