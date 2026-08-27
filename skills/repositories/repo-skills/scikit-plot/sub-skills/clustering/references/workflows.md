# Workflows

Use this reference when you already know you want an elbow curve and need a concrete call pattern.

## Choose K for KMeans
1. Build `X` from the dataset you want to cluster.
2. Start from `KMeans(random_state=1)` or another cloneable clusterer with `n_clusters`.
3. Sweep a small range such as `range(1, 11)` so the knee is easy to read.
4. Call `plot_elbow_curve(clf, X, cluster_ranges=..., n_jobs=1)`.
5. Read the bend where the absolute score stops improving quickly.
6. If you want the runtime overlay, repeat with `show_cluster_time=True`.

Example:
```python
from sklearn.cluster import KMeans
from sklearn.datasets import load_iris
from scikitplot.cluster import plot_elbow_curve

X, _ = load_iris(return_X_y=True)
ax = plot_elbow_curve(KMeans(random_state=1), X, cluster_ranges=range(1, 11))
```

## Compare candidate clusterers or cluster counts
- Use this route only for estimators that can be cloned and refit repeatedly.
- Keep `cluster_ranges` small and ascending.
- Use `n_jobs=1` for notebook or smoke usage; raise it only when the estimator and environment are stable enough to benefit.
- Treat the timing overlay as a relative signal, not a benchmark.

## Embed into an existing figure
- Create `fig, ax = plt.subplots(...)` first.
- Pass `ax=ax` and omit `figsize` if you want to reuse the existing axes.
- Save with `ax.figure.savefig(...)` or close with `plt.close(ax.figure)`.

## Run the bundled smoke script
```bash
python scripts/clustering_smoke.py --start 1 --stop 11 --step 1 --show-cluster-time --output /tmp/scikitplot-elbow.png
```

- Omit `--show-cluster-time` for the curve-only check.
- Use `--n-jobs 1` unless you are deliberately checking parallel execution.
- The script uses the Iris dataset and the Agg backend.

## Native verification signals
- The elbow example uses `KMeans` on Iris with `cluster_ranges=range(1, 11)`.
- The tests exercise missing `n_clusters`, a custom `cluster_ranges` sweep, `ax` reuse, `n_jobs=2`, and `show_cluster_time=False`.
- Treat those behaviors as the minimum smoke-level expectations for this route.

## Route elsewhere
- `../../legacy-factories/SKILL.md` for `clustering_factory`.
- `../../metrics/SKILL.md` for silhouette analysis and other label-based cluster metrics.
