# FEDformer Data Layout

Use this page when the loader cannot find the CSV, the channel counts do not match, or a comparison run needs the same dataset layout across multiple model families.

## Common rules

- `root_path` must point to the directory that contains the CSV file named by `data_path`.
- `data_path` is the CSV filename, not a full path.
- `features` controls the forecast shape:
  - `M` = multivariate input, multivariate output
  - `S` = univariate input, univariate output
  - `MS` = multivariate input, single-target output
- `target` must exist in the CSV when you use `S` or `MS`.
- `enc_in`, `dec_in`, and `c_out` must match the actual feature width for the chosen layout.
- `freq` must match the timestamp cadence in the first column.

## Built-in dataset loaders

| Loader | Expected CSV shape | Timestamp column | Notes |
| --- | --- | --- | --- |
| `ETTh1` / `ETTh2` | `date` + feature columns + `OT` | `date` | Hourly splits. The loader derives train/val/test windows from the canonical ETT length. |
| `ETTm1` / `ETTm2` | `date` + feature columns + `OT` | `date` | Minute-based ETT splits. Minute features are encoded when `timeenc=0`. |
| `custom` | `date` + feature columns + target | `date` | The loader reorders columns so the target is last. Splits are 70% train / 20% test / remainder val. |
| `sin` | `x` + feature columns + `y` | `x` | Synthetic support loader in this fork. It expects `x` and `y` column names. |

## Split behavior

- `train`, `val`, and `test` are determined inside the loader, not by separate files.
- The ETT loaders use fixed canonical borders based on the published dataset sizes.
- The `custom` and `sin` loaders use a 70/20/remaining split.
- All loaders build sliding windows of `[seq_len, label_len, pred_len]`.

## Practical checks

Before launching a long run:

1. Open the CSV and confirm the first column is the time column expected by the loader.
2. Confirm the target column exists and matches the chosen `features` mode.
3. Confirm the forecast widths match the channel count.
4. For custom data, make sure the timestamp column is named `date`.
5. For `sin`, make sure the input has `x` and `y` column names.

## When comparing models

Keep the exact same dataset layout when comparing FEDformer with Autoformer, Informer, or Transformer.
If one model uses `M` and another uses `S` or `MS`, the comparison is no longer apples-to-apples.
