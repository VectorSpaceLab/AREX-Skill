# Prediction Workflow

Use this workflow when you need a custom forecast from a CSV and want the repository to save its prediction output.

## Step 1: Prepare a small fixture

If you need a controlled sample before touching the real CSV, use [`../../../scripts/make_tiny_forecast_csv.py`](../../../scripts/make_tiny_forecast_csv.py). It creates a compact time-series file that exercises the same `date`, target, and covariate layout you plan to use in the real run.

## Step 2: Validate the CSV

Run [`../../../scripts/check_forecast_csv.py`](../../../scripts/check_forecast_csv.py) before training or prediction. It catches:

- missing or unparsable `date` values,
- missing target columns,
- invalid `--cols` selections,
- split-length problems,
- and obvious cadence mismatches.

## Step 3: Choose the custom-data flags

For a real run, the important choices are:

- `--data custom`
- `--root_path` pointing at the CSV directory
- `--data_path` naming the CSV file
- `--features` set to `S`, `M`, or `MS`
- `--target` matching the forecast column
- `--cols` only when you want to restrict or reorder covariates
- `--freq` and `--embed` chosen together
- `--inverse` when you want outputs back on the original scale
- `--do_predict` when you want the prediction branch to save future values

If the custom CSV is still in doubt, stop here and fix the data first.

## Step 4: Smoke test the end-to-end path

Use [`../../../scripts/run_forecasting_smoke.py`](../../../scripts/run_forecasting_smoke.py) when you want a short proof that the custom data path, checkpoint loading, and prediction branch all work together. This is the fastest way to catch schema or cadence mistakes before a long run.

## Step 5: Understand the prediction output

When `--do_predict` is set, the experiment:

1. loads the best checkpoint for the current setting,
2. builds `Dataset_Pred` from the last `seq_len` history rows,
3. extends the timestamp index by `pred_len` future steps, and
4. writes `results/<setting>/real_prediction.npy`.

That file contains the predicted future values only.

## Output map

- `results/<setting>/real_prediction.npy`: future predictions from prediction mode.
- `results/<setting>/pred.npy` and `results/<setting>/true.npy`: test-mode arrays only.
- `results/<setting>/metrics.npy`: test-mode metrics only.
- `checkpoints/<setting>/checkpoint.pth`: the best checkpoint that prediction loads when `load=True`.

## Hand-off rule

If you need benchmark comparison, training schedule changes, checkpoint selection, or metric interpretation, route back to [`../../training-and-evaluation/SKILL.md`](../../training-and-evaluation/SKILL.md).
