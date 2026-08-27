# CLI Evaluation and Metrics

Snips NLU exposes two evaluation commands. They train and evaluate engines from
dataset JSON files and write a metrics JSON report.

## Optional Dependency Gate

The metrics commands import `snips_nlu_metrics` when the command executes. The
base CLI help can be available even when this optional dependency is missing.
If execution fails with `ModuleNotFoundError` or `ImportError` for
`snips_nlu_metrics`, install the Snips NLU metrics extra or a compatible
`snips-nlu-metrics` package in the active environment before rerunning.

## Cross-Validation Metrics

Grammar:

```bash
python -m snips_nlu cross-val-metrics [-c CONFIG_PATH] [-n NB_FOLDS] [-t TRAIN_SIZE_RATIO] [-s] [-i] [-v] dataset_path output_path
```

Example:

```bash
python -m snips_nlu cross-val-metrics -n 5 -t 1.0 -i dataset.json metrics.json
```

Options:

- `dataset_path`: dataset JSON used for all folds.
- `output_path`: destination metrics JSON file. Existing files are overwritten.
- `-c/--config_path`: optional NLU engine config JSON.
- `-n/--nb_folds`: number of folds; default is `5`.
- `-t/--train_size_ratio`: fraction of each training split to train on; default
  is `1.0` and the help describes the valid range as between 0 and 1.
- `-s/--exclude_slot_metrics`: omit slot metrics from the computation.
- `-i/--include_errors`: include parsing errors in the output report.
- `-v/--verbosity`: increase Snips NLU logging; repeat as `-vv` for more detail.

During cross-validation, progress percentages are printed to stdout. The JSON
report may include confusion matrices, F1, precision, recall, and parsing
errors when requested with `-i`.

## Train/Test Metrics

Grammar:

```bash
python -m snips_nlu train-test-metrics [-c CONFIG_PATH] [-s] [-i] [-v] train_dataset_path test_dataset_path output_path
```

Example:

```bash
python -m snips_nlu train-test-metrics -i train_dataset.json test_dataset.json metrics.json
```

Options:

- `train_dataset_path`: dataset JSON used for training.
- `test_dataset_path`: dataset JSON used for evaluation.
- `output_path`: destination metrics JSON file. Existing files are overwritten.
- `-c/--config_path`: optional NLU engine config JSON.
- `-s/--exclude_slot_metrics`: omit slot metrics from the computation.
- `-i/--include_errors`: include parsing errors in the output report.
- `-v/--verbosity`: increase Snips NLU logging; repeat as `-vv` for more detail.

## Choosing a Metrics Command

- Use `train-test-metrics` when the user already has a fixed holdout split or
  needs faster, more predictable command cost.
- Use `cross-val-metrics` when the user has one dataset and wants fold-based
  estimates; expect multiple training runs.
- Add `-i` when debugging bad parses, because it preserves error details in the
  metrics output.
- Add `-s` for intent-only evaluation or when slot metrics are irrelevant to
  the user request.

## Post-Run Checks

```bash
test -s metrics.json
python -m json.tool metrics.json >/dev/null
```

If the output file is absent, empty, or invalid JSON, inspect stderr/stdout for
missing metrics extras, dataset format failures, resource-loading failures, or
engine-training failures. See `troubleshooting.md` for recovery steps.
