# Troubleshooting

## Missing required columns

The helper validates the schema before fitting.

- `admissions_train.csv` must contain `admit`, `gre`, `gpa`, and `prestige`.
- `admissions_test.csv` must contain `gre`, `gpa`, and `prestige`.

If a header has stray whitespace, the helper trims it first. If a required column is still missing, fix the CSV header and rerun.

## Unseen prestige categories

If the test CSV contains a prestige label that was not seen in training, the helper warns and treats that row as the baseline category for the dummy encoding step.

This keeps prediction output usable, but it does not invent a new coefficient for the unseen label. If you need a category-specific coefficient, retrain with training data that includes that label.

## Perfect separation or convergence warnings

`statsmodels` may warn or fail when the data are nearly perfectly separated, the sample is tiny, or the feature matrix is too sparse.

Try one of these fixes:

- Keep the bundled schema intact.
- Reduce overly rare categories.
- Add more training rows.
- Treat the warning as a model-quality issue even if prediction output is still written.

If `Logit.fit` raises a perfect-separation error, the helper stops with a clear message.

## Missing `pandas`, `numpy`, or `statsmodels`

The script needs the scientific Python stack.

- `pandas`, `numpy`, and `statsmodels` are required for fitting.
- `matplotlib` is only needed when you request plots.

If plot support is the only missing piece, rerun with `--no-plots` or omit `--plot-dir`.

## Plot issues

The helper writes the prediction CSV before it starts the optional plotting step. If plotting still fails because of a backend or permissions issue, it warns and continues after the CSV has been written.

- Confirm the plot directory is writable.
- Use `--no-plots` to skip plotting entirely.
- Install `matplotlib` if you want the optional PNG files.
