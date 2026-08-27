# Hyperparameters, Metrics, and Outputs

This reference explains how the search grid is built, how trial winners are chosen, and what gets written to disk after each run.

## Search-space construction

`build_hp_grid(...)` loads `automl_gs/hyperparameters.yml`, merges the `base` block with the selected framework block, filters the keys by the inferred input types and problem type, then samples discrete combinations until it reaches `num_trials` unique trials.

Key implications:

- There are no continuous ranges here; the search is discrete and random.
- Input types matter. If no text columns exist, text-only hyperparameters never enter the grid.
- `num_trials` is a count of sampled hyperparameter combinations, not a number of epochs.
- `num_epochs` is passed through to the generated trainer as epochs for TensorFlow and boosting rounds for XGBoost.

## Hyperparameter families

### Shared across frameworks

- `base_lr`: learning rate / eta.
- `numeric_strat`: numeric encoding strategy (`minmax`, `standard`, `quantiles`, `percentiles`).
- `datetime_month`: include month features for datetime inputs.
- `datetime_year`: include year features for datetime inputs.
- `categorical_strat`: categorical encoding strategy (`all_binary`, `top10_perc`, `top50_perc`).

### TensorFlow-specific

- `weight_decay`
- `batch_size`
- `text_max_length`
- `text_dropout`
- `text_rnn_type`
- `text_rnn_size`
- `text_embed_size`
- `mlp_blocks`
- `mlp_first_size`
- `mlp_size`
- `mlp_dropout`
- `mlp_activation`
- `mlp_regularizer`
- `output_regularizer`
- `reg_objective`

### XGBoost-specific

- `max_depth`
- `gamma`
- `min_child_weight`
- `subsample`
- `colsample_bytree`
- `max_bin`
- `reg_objective`

### Loss-objective reminder

`reg_objective` is a **training loss** choice, not the same thing as `target_metric`. For example:

- TensorFlow regression can try `mse`, `msle`, `mape`, or `poisson` as the loss objective.
- XGBoost regression can try `reg:linear` or `count:poisson`.

Use the `reg_objective` hyperparameter for that choice; use `target_metric` only for selecting the best trial.

## Metrics and objective direction

`metrics.yml` records both display names and whether a metric should be maximized or minimized. The trial-ranking metric is inferred from the target type unless you override it.

### Default ranking metrics

| Problem type | Default `target_metric` | Direction | Notes |
| --- | --- | --- | --- |
| Regression | `mse` | min | `mse`, `mae`, and `r_2` are emitted by the shipped regression callbacks. |
| Binary classification | `accuracy` | max | Metrics also include `log_loss`, `auc`, `precision`, `recall`, and `f1`. |
| Multiclass classification | `accuracy` | max | Metrics also include `log_loss`, `precision`, `recall`, and `f1`. |

### Metric direction cheatsheet

| Metric | Objective | Typical use |
| --- | --- | --- |
| `mse` | min | Default regression ranking metric. |
| `mae` | min | Robust regression ranking metric. |
| `r_2` | max | Variance-explained regression ranking metric. |
| `log_loss` | min | Probability-calibrated classification ranking metric. |
| `accuracy` | max | Default classification ranking metric. |
| `precision` | max | Useful when false positives are expensive. |
| `recall` | max | Useful when false negatives are expensive. |
| `f1` | max | Balanced classification ranking metric. |
| `auc` | max | Ranking-quality metric for binary classification. |
| `categorical_crossentropy` | min | Present in the metric map for compatibility. |
| `binary_crossentropy` | min | Present in the metric map for compatibility. |

### Override guidance

- If you override `target_metric`, make sure the generated callback actually writes that column into `metadata/results.csv` and `automl_results.csv`.
- If you choose a metric with `objective: min`, lower values win.
- If you choose a metric with `objective: max`, higher values win.
- Example: `target_metric='log_loss'` means the best trial is the one with the **lowest** log loss.
- Do not confuse `target_metric` with `reg_objective`; the former ranks trials, the latter changes the training loss.

## Result selection

After each trial:

1. The generated trainer writes `metadata/results.csv` for the current run.
2. The search process appends that trial's rows, plus the sampled hyperparameters, to `automl_results.csv` at the launch directory.
3. The final row in `results.csv` is compared against the current best value.
4. If the metric improved according to the objective direction, the current trial folder is copied into the timestamped best-model folder.
5. The previous best folder is deleted when a new winner appears.

### Important detail

The comparison is based on the selected `target_metric`, not the training loss. For example, a regression search may train with `reg_objective='poisson'` but still rank trials by `mse` unless you deliberately override the ranking metric.

## Output layout

### Per-trial temporary folder

`<model_name>_train`

This folder is recreated for each trial and deleted after the trial finishes.

### Best-model folder

`<model_name>_<framework>_<UTC timestamp>`

The timestamp uses `datetime.utcnow()` and the format `%Y%m%d_%H%M%S`.

Typical contents:

- `model.py`
- `pipeline.py`
- `requirements.txt`
- `encoders/`
- `metadata/`
- framework artifact (`model.bin` for XGBoost, `model_weights.hdf5` or equivalent TensorFlow weights)

### Trial log

`automl_results.csv`

This is the experiment-wide CSV written at the launch directory. It contains:

- `trial_id`
- the per-epoch or per-boosting-round metrics from `metadata/results.csv`
- the sampled hyperparameters for that trial

Use it for experiment comparison, not for post-search artifact execution. The exported model usage belongs in [generated-artifacts](../../generated-artifacts/).
