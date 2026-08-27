# Model-Selection Troubleshooting

## Feature shape problems

Symptoms:
- `ValueError`, singular matrix warnings, or unexpected scalar/1-D arrays.
- Scores vary wildly between runs.

Checks:
- `features` must be a 2-D NumPy array shaped `(N, F)`, not `(F, N)`, `(N, C, H, W)`, or a PyTorch tensor.
- Flatten spatial features with `features.reshape(N, -1)` only when that is the intended representation.
- Remove or investigate NaN/inf values and constant feature columns.
- Use the same feature layer for all candidate models; changing layers changes the score scale.
- If `F` is much larger than `N`, prefer regularized H-score and LogME over vanilla H-score.

## Label problems

Symptoms:
- NaNs from class means.
- Missing classes or inconsistent target class counts.
- Metrics fail after using labels such as `{1, 2, 4}` or string labels.

Checks:
- Convert labels to a 1-D integer NumPy array with one label per sample.
- Reindex target labels to contiguous `0..C_t-1` because TLLib infers class count as `labels.max() + 1`.
- Ensure every target class expected in the ranking subset has at least one sample; tiny per-class counts make covariance and evidence estimates unreliable.
- Keep `features[i]`, `predictions[i]`, and `labels[i]` aligned to the same target sample.

## Predictions, logits, and log-probabilities

Symptoms:
- LEEP returns NaN/inf or extremely low values.
- LEEP/NCE disagree because source predictions are malformed.

Checks:
- LEEP requires probabilities, not raw logits or log-probabilities.
- Convert logits with a numerically stable softmax:

```python
prob = np.exp(logits - logits.max(axis=1, keepdims=True))
prob = prob / prob.sum(axis=1, keepdims=True)
```

- Convert log-probabilities with `np.exp(log_probs)` and renormalize rows.
- Validate `predictions.shape == (N, C_s)`, `predictions >= 0`, and row sums close to `1`.
- Avoid all-zero source probability columns. LEEP divides by the total probability assigned to each source class.
- For NCE, pass source class ids such as `predictions.argmax(axis=1)`, not probability rows.

## Singular covariance and numerical issues

Symptoms:
- H-score unstable with duplicated samples or high-dimensional features.
- LogME returns NaN/inf.
- TransRate changes drastically with tiny feature perturbations.

Checks:
- Standardize the extraction pipeline and remove all-constant features.
- Increase target ranking samples, especially per class.
- Try `regularized_h_score` when vanilla H-score is unstable.
- Cast features to `float64` before ranking when precision is a concern.
- For TransRate, keep `eps` fixed across candidates; adjust it only to resolve numerical instability and document the value.
- LogME uses JIT-compiled internals; the first call may be slower and should not be mistaken for a hang on large arrays.

## Saving and reusing features

Symptoms:
- A ranking run appears successful but ranks the wrong model.
- Features and predictions have matching shapes but inconsistent values.

Checks:
- Store cache metadata with model name, checkpoint, dataset, split, preprocessing, feature layer, package versions, and array shapes.
- Invalidate caches after changing transforms, model weights, classifier head, source label space, or target split.
- Save probabilities after softmax if using LEEP; save logits separately only if metadata says so.
- Do not mix arrays from different candidates or data orders. Re-run a small sample-id audit when possible.

## Metric interpretation limits

Symptoms:
- Highest transferability score does not produce the best fine-tuned accuracy.
- Metrics disagree across candidates.

Interpretation rules:
- Compare scores only within the same target dataset/split/preprocessing/layer/candidate set.
- Higher scores are generally better, but absolute values are not portable across datasets or feature layers.
- LEEP/NCE need a meaningful source classifier head; they are less informative when the head is unrelated to the target domain or was replaced.
- Feature metrics can favor separable representations that still need careful fine-tuning, regularization, or augmentation.
- Treat close rankings as ties and validate shortlisted models with a real fine-tuning run through [task-generalization](../../task-generalization/SKILL.md).

## Installation/API compatibility

Symptoms:
- `ModuleNotFoundError: tllib`.
- `ImportError` for `regularized_h_score` or `transrate` from `tllib.ranking`.

Checks:
- Run the bundled smoke script in an environment where the `tllib` package is installed.
- Import `regularized_h_score` from `tllib.ranking.hscore` and `transrate` from `tllib.ranking.transrate`.
- Ensure NumPy, scikit-learn, and numba are installed for the metric set used here.
