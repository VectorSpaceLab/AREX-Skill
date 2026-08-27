# KMeans Troubleshooting

## Initialization errors

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Must specify one of k or centroids` | Constructor lacks both cluster count and explicit centroids. | Pass `KMeans(k=...)` or `KMeans(centroids=...)`. |
| `k` validation failure | `k` is below 2, non-integer, or invalid tensor scalar. | Use an integer `k >= 2`. |
| Invalid `init` value | Initializer is not one of the supported strings. | Use `'first-k'`, `'random'`, `'submodular-facility-location'`, or `'submodular-feature-based'`. |
| Submodular initializer fails | `apricot-select`/`numba` problem or unsuitable data. | Start with `first-k` or `random`; use submodular initializers only after the basic path works. |

## Data and centroid shapes

- `X` should be 2D `(n, d)`.
- Explicit `centroids` should be 2D `(k, d)`.
- Prediction data must have the same feature dimension as fitted centroids.
- KMeans distance computations use numeric tensors; convert categorical/string columns before fitting.

## Sample weights

- Weights must be nonnegative.
- A 1D weight vector should have one entry per example.
- A 2D weight matrix should be compatible with the shape of `X`.
- If assignments look wrong under weights, compare to an unweighted tiny subset first.

## Convergence and interpretation

- Cluster ids are arbitrary and depend on initialization order.
- If `fit_predict` returns unexpected labels, inspect `model.centroids` rather than relying on label numbers.
- Increase `max_iter` or lower `tol` when centroids stop too early.
- Use `random_state` for reproducible `random` or submodular initializations.
- `frozen=True` or `inertia=1.0` prevents effective centroid movement.

## Masked data

The implementation accounts for masked tensors in distance and centroid initialization paths, but masked KMeans workflows should be validated on a tiny fixture before being trusted on production data. Preserve the `mask=True means observed` convention from PyTorch masked tensors.
