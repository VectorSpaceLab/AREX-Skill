# Metrics reference

`pyhealth.metrics` exports `binary_metrics_fn`, `multiclass_metrics_fn`,
`multilabel_metrics_fn`, `regression_metrics_fn`, `ranking_metrics_fn`, and
`ddi_rate_score`. The current binary signature is:

```text
binary_metrics_fn(y_true: numpy.ndarray, y_prob: numpy.ndarray,
                  metrics: Optional[List[str]] = None,
                  threshold: float = 0.5) -> Dict[str, float]
```

With no metric list, binary defaults to `pr_auc`, `roc_auc`, and `f1`.
Supported binary names include PR-AUC, ROC-AUC, accuracy,
balanced_accuracy, f1, precision, recall, Cohen's kappa, Jaccard, `ECE`, and
`ECE_adapt`. Probabilities are thresholded for discrete metrics; preserve raw
probabilities for ranking/calibration metrics.

## Shape routing

- **Binary:** `y_true` and `y_prob` are aligned one-dimensional arrays.
- **Multiclass:** use a class axis and the package's expected label/probability
  convention; confirm with the function docstring/source.
- **Multilabel:** use aligned `(n_samples, n_labels)` arrays and choose a
  threshold/protocol deliberately; drug recommendation often belongs here.
- **Regression:** use continuous target/prediction arrays.
- **Ranking:** preserve candidate ordering and group/query identity.
- **Generative/fairness/interpretability:** inspect their dedicated API and
  document the reference distribution, subgroup, or explanation target.

Do not compare metrics from different splits, label encodings, or threshold
policies as if they were the same experiment. Handle single-class validation
sets and missing labels explicitly; ROC-AUC may be undefined.
