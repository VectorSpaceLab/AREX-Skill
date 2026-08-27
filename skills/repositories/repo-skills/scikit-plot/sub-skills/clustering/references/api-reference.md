# API Reference

Read this for the exact arguments, return behavior, and implementation constraints of `plot_elbow_curve`.

## `plot_elbow_curve`

`plot_elbow_curve(clf, X, title='Elbow Plot', cluster_ranges=None, n_jobs=1, show_cluster_time=True, ax=None, figsize=None, title_fontsize="large", text_fontsize="medium") -> matplotlib.axes.Axes`

| Argument | Verified behavior |
| --- | --- |
| `clf` | Must expose `n_clusters`; it is cloned for each candidate K, then fit and scored. Use a sklearn-style clusterer so `clone()` works. |
| `X` | Array-like data passed to `fit(X)` and `score(X)`. |
| `cluster_ranges` | If omitted, defaults to `range(1, 12, 2)`. Provided values are sorted before plotting. Keep the sweep finite and non-empty. |
| `n_jobs` | Forwarded to `joblib.Parallel`. Larger values may add process overhead. |
| `show_cluster_time` | When `True`, adds a secondary axis with elapsed seconds per cluster count. |
| `ax` | Reuses an existing Matplotlib `Axes`; otherwise a new figure and axes are created. |
| `figsize` | Only used when `ax` is `None`. |
| `title_fontsize`, `text_fontsize` | Passed through to Matplotlib text APIs. |

## Implementation notes
- The curve uses `np.absolute(score)` and is labeled as sum of squared errors.
- The source path clones the estimator, sets `n_clusters`, and calls `fit(X).score(X)` for each candidate value.
- The current implementation does not call `fit_predict`, even though the docstring names it.
- The return value is the main `Axes`; the timing overlay, if requested, is attached with `twinx()`.

## Good fit
- Best for KMeans-like clusterers whose score is inertia-like and comparable across candidate K values.
- For custom clusterers, match the sklearn estimator protocol (`clone` must succeed) and ensure the score semantics still make sense as an elbow curve.

## Related routes
- `../../legacy-factories/SKILL.md` for `clustering_factory`.
- `../../metrics/SKILL.md` for silhouette plots built from cluster labels.
