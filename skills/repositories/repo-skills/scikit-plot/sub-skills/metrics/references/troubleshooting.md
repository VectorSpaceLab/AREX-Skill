# Metrics troubleshooting

If the package fails before a metric function is called, read the root `../../../references/troubleshooting.md` first. This repository snapshot was verified with `scipy<1.11` and `matplotlib<3.9`.

## Common failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ValueError: Invalid argument for curves` | Legacy `plot_roc_curve` or `plot_precision_recall_curve` received a bad `curves` value. | Use only `micro`, `macro`, and/or `each_class`, or migrate to `plot_roc` / `plot_precision_recall`. |
| `Cannot calculate KS statistic for data with ... category/ies` | `plot_ks_statistic` received non-binary labels. | Use a binary target or switch to ROC/PR for multiclass. |
| `plot_calibration_curve only works for binary classification` | Calibration curve target has more than two classes. | Filter to a binary one-vs-rest task or choose another diagnostic. |
| `y_true takes value in {'1', 'A'} and pos_label is not specified` | Modern scikit-learn cannot infer a positive label for string-encoded binary labels, and this scikit-plot wrapper does not expose `pos_label`. | Encode binary labels as `{0, 1}` or `{-1, 1}` before calling `plot_calibration_curve`. |
| `Cannot calculate Cumulative Gains` or `Cannot calculate Lift Curve` | Cumulative gain/lift input is not binary. | Use binary labels and a two-column probability matrix. |
| `` `probas_list` does not contain a list `` | Calibration input was a single array rather than a list of arrays. | Wrap probability arrays as `probas_list=[probas]`. |
| `Length ... of clf_names does not match length ... of probas_list` | Calibration curve labels do not match the number of score arrays. | Provide one classifier name per array or omit `clf_names`. |
| `invalid shape` for a probability array | Probability/scores shape does not match `y_true`. | Use a `(n_samples, n_classes)` matrix for most probability plots, or a 1-D score vector only where calibration allows it. |
| duplicate or absent labels in confusion matrix | `true_labels` or `pred_labels` contains duplicates or labels not present in `labels`. | Validate display labels before plotting or let scikit-plot infer labels. |
| the figure goes to a new plot instead of your subplot | `ax` was omitted. | Create `fig, ax = plt.subplots()` and pass `ax=ax`. |

## Debug sequence

1. Run the root environment smoke script.
2. Print `np.asarray(y_true).shape`, `np.asarray(y_pred).shape`, and `np.asarray(y_probas).shape`.
3. Verify class order: `np.unique(y_true)` should match the probability columns returned by the classifier.
4. For binary-only functions, confirm exactly two classes before plotting.
5. Pass `ax=` explicitly if figure composition matters.
6. If a legacy alias fails, retry with the current API name and options.

## Minimal invalid-input checks

Use these as quick assertions while debugging user data:

```python
import numpy as np
classes = np.unique(y_true)
assert y_probas.shape[0] == len(y_true)
assert y_probas.ndim == 2
assert y_probas.shape[1] == len(classes)
```

For calibration curves, a 1-D decision-score vector is acceptable, but it must still have one score per sample.
