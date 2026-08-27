# CSV and Feature Rules

## CSV schema

Custom time-series CSVs must provide:

- `date`: a column that pandas can parse into timestamps.
- `target`: the forecast column, named exactly as passed to `--target`.
- Covariates: zero or more additional numeric feature columns.

Key loader behavior:

- The custom loader always reorders columns to `date + selected_covariates + target`.
- If `--cols` is provided, the loader copies that list, removes the target from it, and then appends the target at the end.
- Therefore `--cols` must include the target exactly once. If it does not, the loader fails before training or prediction.
- If `--cols` is omitted, the loader uses every non-`date` column and still moves the target to the end.

## Feature mode matrix

| Mode | Input columns after `date` | Output channels | Set `enc_in` / `dec_in` / `c_out` | Notes |
| --- | --- | --- | --- | --- |
| `S` | target only | target only | `1 / 1 / 1` | Univariate forecast. The dataset keeps only the target column. |
| `M` | all selected columns | all selected columns | channel count / channel count / channel count | Multivariate forecast of every channel. |
| `MS` | all selected columns | target only | channel count / channel count / `1` | Multivariate inputs, single-target output. The loss path uses the last channel only. |

Additional points:

- For custom data, the model dimensions are not auto-filled from a preset. Set `enc_in`, `dec_in`, and `c_out` yourself.
- `Dataset_Custom` and `Dataset_Pred` both follow the same column ordering rule before slicing.

## Row-count and split guidance

`Dataset_Custom` uses an approximate `70% / 10% / 20%` split:

- `train = int(0.7 * N)`
- `test = int(0.2 * N)`
- `val = N - train - test`

The loader then shifts the validation and test starts backward by `seq_len` rows so those splits have encoder context.

Implications:

- The ratios are approximate because of integer truncation.
- The training split needs at least one `seq_len + pred_len` window.
- Validation and test starts are shifted backward by `seq_len`, so their post-split portions must each cover at least `pred_len` rows.
- If any computed split length is zero or negative, the data loader breaks.
- Prediction mode is lighter: `Dataset_Pred` only needs the final `seq_len` source rows because the future timestamps are synthesized.

## Frequency and time-feature notes

There are two time-feature paths:

- `--embed fixed` or `--embed learned` keeps `timeenc=0` and uses discrete calendar fields from the parsed dates.
- `--embed timeF` switches to `timeenc=1` and uses frequency-aware continuous time features.

Supported cadence behavior:

- `timeenc=0` expects the lower-case cadence codes `y`, `m`, `w`, `d`, `b`, `h`, or `t`.
- `timeenc=1` routes through the frequency helper, which accepts the offset classes it can map from pandas frequency strings.
- Unsupported or mismatched frequencies surface as helper errors, not silent fallbacks.

Prediction-time detail:

- Training and evaluation use the shortened cadence code.
- Prediction keeps the original detailed cadence string so the future timestamps can be extended from the user-supplied frequency.
- If cadence handling is unclear, prefer the canonical short code and validate with the smoke helper before a long run.

## `--cols` target inclusion gotcha

When `--cols` is used:

- the target must appear in the list,
- it must appear only once,
- and it will be removed from the feature list before being appended back as the last column.

If you want the loader to infer all covariates automatically, omit `--cols`.
