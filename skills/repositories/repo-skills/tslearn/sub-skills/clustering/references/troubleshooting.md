# Troubleshooting: Clustering

Use this checklist when tslearn clustering results look wrong, unstable, or fail before you can score them.

## Empty clusters

Symptoms:

- `EmptyClusterError` from a custom loop or a direct call into the shared clustering helpers.
- A centroid-based fit ends without useful fitted attributes.
- Labels collapse into one cluster after a brittle initialization.

Actions:

1. Reduce `n_clusters`.
2. Increase `n_init`.
3. Change `init` from a brittle guess to `"k-means++"`, `"random"`, or a better centroid array.
4. Tighten the metric parameters only after the cluster count and initialization are sensible.
5. For `KernelKMeans`, avoid `sigma="auto"` on tiny data if the kernel degenerates.

## Metric mismatches

Symptoms:

- Ragged input passed to `metric="euclidean"` or `KShape`.
- A square distance matrix is required but the raw time series were passed instead.
- `silhouette_score` complains because the score metric does not match the input form.

Actions:

1. Use `to_time_series_dataset(...)` to make ragged input explicit.
2. Resample or pad before Euclidean KMeans or KShape.
3. Use `metric="precomputed"` only with a square distance matrix and labels in the same order.
4. For clustering validation, score with the same geometry that produced the labels.

## Bad normalization

Symptoms:

- KShape groups by amplitude instead of shape.
- Euclidean KMeans is dominated by scale differences.
- The same data cluster differently before and after scaling.

Actions:

1. For KShape, scale first with `TimeSeriesScalerMeanVariance(mu=0., std=1.)`.
2. If amplitude should not matter for Euclidean KMeans, scale before clustering.
3. If shifts matter more than absolute amplitude, switch to DTW or Soft-DTW KMeans.

## Random-state sensitivity

Symptoms:

- Small datasets give different partitions across runs.
- One seed looks good and the next seed looks wrong.
- Kernel k-means changes substantially even though the data are fixed.

Actions:

1. Fix `random_state`.
2. Raise `n_init`.
3. Compare `metric="euclidean"` and `metric="dtw"` on the same tiny dataset before changing preprocessing.
4. For GAK, set an explicit positive `sigma` instead of relying on `sigma="auto"`.

## Silhouette pitfalls

Symptoms:

- The silhouette score is undefined, trivial, or misleading.
- You computed a precomputed score from a matrix that does not match the labels.

Actions:

1. Check that you have at least two non-empty clusters.
2. Use `metric="dtw"` for DTW-based partitions, `metric="softdtw"` for Soft-DTW partitions, and `metric="euclidean"` for Euclidean partitions.
3. When using `metric="precomputed"`, make sure the matrix is square and aligned to the same sample order.
4. Treat DBSCAN noise labels carefully; `-1` is a noise label, not a centroid.

If the problem is not clustering-specific, return to the [tslearn router](../../../SKILL.md) and route into the relevant sibling sub-skill.
