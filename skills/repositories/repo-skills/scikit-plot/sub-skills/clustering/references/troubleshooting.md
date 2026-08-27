# Troubleshooting

## Import fails before plotting starts
**Symptom:** `ImportError: cannot import name 'interp' from 'scipy'` or the smoke script aborts while importing `scikitplot.cluster`.

**Likely cause:** the environment is too new for this 0.3.7 snapshot.

**Recovery:** install a compatible stack. The verified pins for this repo snapshot were `scipy<1.11` and `matplotlib<3.9`.

**Next check:** rerun `python scripts/clustering_smoke.py --help` and then the smoke command.

## Missing `n_clusters`
**Symptom:** `TypeError: "n_clusters" attribute not in classifier. Cannot plot elbow method.`

**Likely cause:** the object is not a clusterer or does not expose `n_clusters`.

**Recovery:** use `KMeans` or another sklearn-style clusterer that stores `n_clusters`. If you only have labels and want cluster quality curves, route to `metrics` instead.

## Clone / fit / score mismatch
**Symptom:** `clone` fails, `fit(X)` fails, or `score(X)` is missing.

**Likely cause:** the estimator does not follow sklearn clone conventions, or its `score` does not represent a comparable elbow objective.

**Recovery:** adapt the estimator to the sklearn protocol before using this sub-skill, or do the comparison outside scikit-plot.

## Parallel or timing behavior looks noisy
**Symptom:** the timing axis jumps around, or `n_jobs > 1` is slower than expected.

**Likely cause:** process startup overhead, tiny datasets, or a custom estimator that is expensive to clone.

**Recovery:** keep `n_jobs=1` for smoke and interactive use. Use `show_cluster_time=False` when you only need the elbow curve.

## Cluster sweep is empty or awkward
**Symptom:** no meaningful curve or a failure while unpacking the results.

**Likely cause:** `cluster_ranges` was empty, invalid, or too large for the environment.

**Recovery:** pass a small finite ascending sweep such as `range(1, 11)` and keep values distinct.
