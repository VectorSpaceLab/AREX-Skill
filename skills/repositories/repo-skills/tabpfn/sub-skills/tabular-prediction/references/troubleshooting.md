# Core Prediction Troubleshooting

## Output choices

| Symptom | Cause | Fix |
| --- | --- | --- |
| `Invalid output type` on regression | `output_type` is not one of `mean`, `median`, `mode`, `quantiles`, `main`, or `full` | Use a supported string; use `full` only when distribution internals are needed. |
| `All quantiles must be between 0 and 1 and floats` | Quantiles are integers, strings, or outside `[0, 1]` | Pass floats such as `[0.1, 0.5, 0.9]`. |
| `softmax(predict_logits(X))` does not match `predict_proba(X)` | Multiple estimators with probability averaging after softmax | Use `predict_proba` for probabilities; use `predict_raw_logits` plus `logits_to_probabilities` for custom analysis. |
| `predict_raw_logits` shape surprises users | It returns per-estimator logits | Expect `(n_estimators, n_samples, n_classes)`. |

## Input and label mistakes

- `X` must be two-dimensional and have the same number of rows as `y` at fit.
- Classification labels must be valid classification targets and cannot contain NaNs.
- Regression targets should be numeric.
- DataFrame dtype, text, categorical, NaN, and infinity questions belong in preprocessing-config.

## CPU limits

When running on CPU, TabPFN raises on large datasets by default because local CPU
inference is slow. For current `v3`, the default CPU limit is 5000 samples; older
versions use 1000. Use a GPU, downsample, or explicitly set the CPU override only
when the user accepts the runtime cost.

## Model access and downloads

A first `fit` may need model weights. If the error mentions license acceptance,
HuggingFace gated access, `TABPFN_TOKEN`, or cache directories, route to
model-management instead of debugging prediction code.
