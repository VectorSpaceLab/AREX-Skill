# Supervised, densMAP, clustering, and outlier workflows

These recipes use tiny local sklearn fixtures. They avoid plotting, network
access, downloads, large image datasets, and long training runs.

## Supervised UMAP with full labels

Use this when every row has a reliable class label and the embedding should
respect both feature geometry and label topology.

```python
from sklearn.datasets import load_iris
from umap import UMAP

X, y = load_iris(return_X_y=True)
mapper = UMAP(
    n_neighbors=10,
    min_dist=0.05,
    target_metric="categorical",
    target_weight=0.5,
    random_state=42,
)
embedding = mapper.fit_transform(X, y)
```

Guidance:

- `y` must have one value per row in `X` and the same row order.
- `target_metric="categorical"` is the default for class labels.
- Compare with an unsupervised UMAP baseline before claiming labels improved the
  analysis.
- Record `target_metric`, `target_weight`, and `random_state` with the result.

## Semi-supervised UMAP with partial labels

Use this when some rows are unlabeled but still useful for the data manifold.
For categorical targets, `-1` is treated as an unlabeled value.

```python
from sklearn.datasets import make_blobs
from umap import UMAP

X, y = make_blobs(n_samples=120, centers=3, cluster_std=0.75, random_state=42)
y = y.copy()
y[::5] = -1

mapper = UMAP(
    target_metric="categorical",
    target_weight=0.3,
    random_state=42,
)
embedding = mapper.fit_transform(X, y)
```

Guidance:

- Keep the `-1` convention for categorical semi-supervision; do not assume it
  works the same way for continuous target metrics.
- Start with a lower or moderate `target_weight` when labels are sparse or
  noisy, then validate on known labels or held-out rows.
- Keep `target_n_neighbors=-1` unless you intentionally want target
  neighborhoods to differ from feature neighborhoods.

## Metric learning and held-out projection

Fit a label-aware embedding on training rows, then project new unlabeled rows
with `transform` when you need supervised feature engineering.

```python
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from umap import UMAP

X, y = load_iris(return_X_y=True)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42, stratify=y
)

mapper = UMAP(n_neighbors=15, random_state=42).fit(X_train, y_train)
test_embedding = mapper.transform(X_test)
```

Do not use densMAP for this pattern: densMAP models do not support transforming
new data into an existing embedding.

## Continuous or structured targets

For regression-like or numeric targets, choose a metric appropriate to the target
space instead of the default categorical metric.

```python
mapper = UMAP(
    target_metric="l2",
    target_weight=0.5,
    target_n_neighbors=10,
    random_state=42,
).fit(X, y_continuous)
```

Use `target_metric_kwds` only when the selected target metric needs additional
arguments.

## densMAP for density preservation

Use densMAP when relative local density is part of the question, not merely when
you want more separated clusters.

```python
from sklearn.datasets import load_iris
from umap import UMAP

X, y = load_iris(return_X_y=True)
mapper = UMAP(
    densmap=True,
    dens_lambda=2.0,
    dens_frac=0.3,
    random_state=42,
)
embedding = mapper.fit_transform(X, y)
```

Guidance:

- Higher `dens_lambda` emphasizes density preservation more strongly.
- `dens_frac` controls what fraction of epochs use the density objective.
- densMAP usually costs more runtime than standard UMAP.
- densMAP can be supervised by passing `y`, but density and label separation are
  still objectives to validate rather than guaranteed improvements.

## Density outputs

Use `output_dens=True` when you need local-radius diagnostics.

```python
embedding, rad_orig, rad_emb = UMAP(
    densmap=True,
    output_dens=True,
    random_state=42,
).fit_transform(X, y)
```

`rad_orig` and `rad_emb` are log-radius summaries of local density in the
original space and embedding space. They are diagnostic outputs, not automatic
cluster labels or anomaly labels.

## UMAP-assisted clustering

UMAP can make clustering easier for some datasets, especially when density-based
methods struggle in high dimensions. It can also create visually convincing but
false separations, so validate.

```python
from sklearn.cluster import KMeans
from sklearn.datasets import make_blobs
from sklearn.metrics import adjusted_mutual_info_score, adjusted_rand_score
from umap import UMAP

X, y = make_blobs(n_samples=120, centers=3, cluster_std=0.75, random_state=42)
embedding = UMAP(
    n_neighbors=20,
    min_dist=0.0,
    n_components=2,
    random_state=42,
).fit_transform(X)
labels = KMeans(n_clusters=3, n_init=10, random_state=42).fit_predict(embedding)
print(adjusted_rand_score(y, labels), adjusted_mutual_info_score(y, labels))
```

For HDBSCAN, install the optional `hdbscan` package yourself and treat it as a
separate downstream dependency. The bundled smoke helper only imports HDBSCAN
when `--cluster-method hdbscan` is requested.

Validation checklist:

1. Compare multiple UMAP and clustering parameter settings.
2. Prefer labels, ARI/AMI, stability, silhouette-style scores, or domain review
   over visual inspection alone.
3. Try `n_components > 2` when clustering quality matters more than plotting.
4. Do not call UMAP clusters ground truth without external evidence.

## Outlier and exploratory analysis

A low-dimensional UMAP embedding can speed up LOF-style outlier review, but the
embedding may hide or invent apparent isolation.

```python
from sklearn.neighbors import LocalOutlierFactor

outlier_mask = LocalOutlierFactor(contamination=0.05).fit_predict(embedding) == -1
```

For difficult outlier work:

- Compare outliers in the original feature space and the embedding space.
- Compare multiple seeds or neighborhood sizes.
- Consider lower `set_op_mix_ratio` values only as an experiment for preserving
  disconnected/outlying structure, then validate the result.
- Avoid deleting or filtering samples solely because they look isolated in a
  2D UMAP view.

## Large examples are reference-only patterns

Workflows based on large image datasets, OpenML downloads, HDBSCAN-heavy runs,
or saved figures are not safe defaults for a Researcher session. First reproduce
the pattern on a bundled toy workflow, then ask for explicit permission before
downloads, storage-heavy data, or long runs.
