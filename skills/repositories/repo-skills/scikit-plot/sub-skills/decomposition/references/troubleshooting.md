# Decomposition troubleshooting

Read root troubleshooting first if `import scikitplot` fails. This repository snapshot was verified with `scipy<1.11` and `matplotlib<3.9`.

## Failure surfaces

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `TypeError: "clf" does not have explained_variance_ratio_ attribute. Has the PCA been fitted?` | PCA was not fitted or the estimator does not expose explained variance ratios. | Call `pca.fit(X)` before `plot_pca_component_variance`, or use a PCA-like estimator that exposes `explained_variance_ratio_`. |
| Projection fails inside `transform` | PCA was not fitted or `X` has a different feature count than the data used for fitting. | Fit the estimator on the same preprocessing space and feature schema used for plotting. |
| Projection fails with an index error or a blank second axis | The transformed output has fewer than two dimensions. | Fit with `n_components=2` or greater. |
| Biplot labels are wrong or fail by index | `feature_labels` length does not match the original feature count. | Pass one label per input feature or omit `feature_labels`. |
| Biplot is unreadable | Too many features or large component vectors crowd the figure. | Set `biplot=False`, preselect features, or use a larger figure. |
| Plot lands on a new figure | `ax` was omitted. | Create and pass an explicit axes. |

## Debug checklist

1. Confirm the PCA object is fitted.
2. Print `X.shape` and `pca.components_.shape`.
3. Confirm `pca.transform(X).shape[1] >= 2` for projection.
4. Confirm `len(feature_labels) == X.shape[1]` before biplotting.
5. Use `scripts/decomposition_smoke.py` to separate package/runtime issues from user-data issues.
