# Workflows

This sub-skill packages the admissions logistic-regression example adapted from the source admissions script plus the bundled CSV fixtures. The helper is Python 3-only and can run from any working directory when you pass explicit paths.

## 1) Fit the model and write predictions

Use the copied fixtures under `references/data/`.

```bash
python3 scripts/statsmodels_admission_logit.py \
  --train references/data/admissions_train.csv \
  --test references/data/admissions_test.csv \
  --output ./admissions_predictions.csv \
  --no-plots
```

What this does:

1. Reads the bundled train/test CSVs.
2. Validates the required columns and trims header whitespace.
3. Converts `prestige` into dummy columns with `best` as the reference level when available.
4. Adds an intercept term and fits `statsmodels.api.Logit`.
5. Writes a CSV that keeps the original test columns and appends `admit_pred` and `admit_yn`.

## 2) Generate optional plots

Use `--plot-dir` when you want non-interactive PNG diagnostics.

```bash
python3 scripts/statsmodels_admission_logit.py \
  --train references/data/admissions_train.csv \
  --test references/data/admissions_test.csv \
  --output ./admissions_predictions.csv \
  --plot-dir ./admissions_plots
```

Typical plot files:

- `gpa_histogram.png`
- `gre_by_admit.png`
- `predicted_probability_hist.png`

## 3) Adjust the yes/no threshold

The default threshold is `0.5`. Raise it to make `admit_yn=yes` more conservative.

```bash
python3 scripts/statsmodels_admission_logit.py \
  --train references/data/admissions_train.csv \
  --test references/data/admissions_test.csv \
  --output ./admissions_predictions.csv \
  --threshold 0.6 \
  --no-plots
```

## 4) Check the CLI

```bash
python3 scripts/statsmodels_admission_logit.py --help
```

Keep every command pointed at the bundled copies in `references/data/`; do not use the original source paths or hardcoded OS-specific paths.
