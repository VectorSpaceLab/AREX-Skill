---
name: custom-data-and-prediction
description: "Prepare custom time-series CSVs, validate feature/target/frequency
  choices, run the repository prediction path, and troubleshoot data-loader
  failures for Informer2020 custom data jobs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Custom Data and Prediction

Use this sub-skill for `--data custom` jobs that start from a custom time-series CSV and need a safe path to validation, prediction, or loader debugging.

## Read First

- [`references/data-formats.md`](references/data-formats.md)
- [`references/prediction-workflow.md`](references/prediction-workflow.md)
- [`references/troubleshooting.md`](references/troubleshooting.md)
- [`../../scripts/make_tiny_forecast_csv.py`](../../scripts/make_tiny_forecast_csv.py)
- [`../../scripts/check_forecast_csv.py`](../../scripts/check_forecast_csv.py)
- [`../../scripts/run_forecasting_smoke.py`](../../scripts/run_forecasting_smoke.py)

## Route Here When

- The CSV is user-provided and must be shaped for the custom data loader.
- You need to choose or validate `--features` (`S`, `M`, `MS`), `--target`, `--cols`, `--freq`, `--embed`, or `--inverse`.
- You need to understand how `Dataset_Custom` or `Dataset_Pred` will slice, scale, and reorder the data.
- You need the prediction output name or a minimal smoke path before larger runs.

## Delegate Elsewhere

- [`../training-and-evaluation/SKILL.md`](../training-and-evaluation/SKILL.md) for benchmark preset choice, hyperparameter tuning, checkpoint strategy, and metrics interpretation.
- Other sub-skills for model architecture, attention internals, or non-forecasting tasks.

## Standard Handoff

1. Confirm the CSV schema, target name, and feature mode.
2. Check that the split is long enough for the chosen `seq_len` and `pred_len`.
3. Validate the file with the shared CSV checker; use the tiny fixture or smoke helper when you need a minimal end-to-end proof.
4. Run prediction with `--do_predict` when you want `results/<setting>/real_prediction.npy`; keep checkpoint and metric decisions with the training-and-evaluation skill.

## Safe Defaults

- Keep the target in `--cols` whenever you supply `--cols`.
- Match `enc_in`, `dec_in`, and `c_out` to the selected feature mode and channel count.
- Prefer canonical frequency codes when both training and prediction must use the same cadence.
- Treat missing dates, too-short splits, and loader exceptions as data issues first.
