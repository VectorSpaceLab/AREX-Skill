# Exploration reference

This reference covers exploratory Orange3 APIs behind visualization and unsupervised widgets. It assumes data loading and domain construction are already handled by `data-preparation`.

Verified environment facts:

- Orange runtime: `Orange.__version__ == 3.41.0.dev` from the editable inspection install.
- Required backend: CPU + Qt GUI packages; no accelerator backend is required.
- Safe GUI imports run under `QT_QPA_PLATFORM=offscreen`.
- Core live checks succeeded for distances, `KMeans`, `DBSCAN`, hierarchical clustering, `PCA`, `RadViz`, `DomainBasicStats`, `SOM.prepare_data`, and selected widget imports.

## Core object flow

| Object | Produced by | Consumed by | Notes |
| --- | --- | --- | --- |
| `Orange.data.Table` | sibling data-preparation workflows | all plotting, projection, clustering, and statistics APIs | This sub-skill assumes the table already exists. |
| `Orange.misc.DistMatrix` | `Orange.distance.*`, `OWDistances`, `DistMatrix.from_file` | `OWDistanceMatrix`, `OWDistanceMap`, `OWHierarchicalClustering`, `OWMDS`, `OWtSNE`, `OWSilhouettePlot` | Carries `row_items`, `col_items`, and `axis`; many widgets require a square symmetric matrix. |
| `Orange.projection.Projection` / `DomainProjection` | `PCA`, `FreeViz`, `RadViz`, `TSNE`, etc. | callable on compatible `Table` data | Projection models add computed continuous coordinates to a transformed domain. |
| `Orange.clustering.ClusteringModel` | `KMeans(...).get_model(data)`, `DBSCAN(...).get_model(data)`, `Louvain(...).get_model(data)` | callable when the clusterer supports prediction; widgets use it for computed cluster columns | `KMeansModel` predicts new compatible rows; DBSCAN-style models generally do not predict new rows. |

## Distances and `DistMatrix`

Public distance constructors verified by introspection:

```python
Euclidean(e1=None, e2=None, axis=1, impute=False, normalize=False, callback=None)
Manhattan(e1=None, e2=None, axis=1, impute=False, normalize=False, callback=None)
Cosine(e1=None, e2=None, axis=1, impute=False, callback=None, *, similarity=False, **kwargs)
Jaccard(e1=None, e2=None, axis=1, impute=False, callback=None, *, similarity=False, **kwargs)
SpearmanR(e1=None, e2=None, axis=1, impute=False, callback=None, *, similarity=False, **kwargs)
SpearmanRAbsolute(e1=None, e2=None, axis=1, impute=False, callback=None, *, similarity=False, **kwargs)
PearsonR(e1=None, e2=None, axis=1, impute=False, callback=None, *, similarity=False, **kwargs)
PearsonRAbsolute(e1=None, e2=None, axis=1, impute=False, callback=None, *, similarity=False, **kwargs)
Mahalanobis(e1=None, e2=None, axis=1, impute=False, callback=None, *, similarity=False, **kwargs)
Hamming(e1=None, e2=None, axis=1, impute=False, callback=None, *, similarity=False, **kwargs)
Bhattacharyya(e1=None, e2=None, axis=1, impute=False, callback=None, *, similarity=False, **kwargs)
```

Use API `axis=1` for row distances and `axis=0` for column/feature distances. `OWDistances` presents this as "Rows" and "Columns" but internally flips its setting to the API axis; when writing code, follow the constructor signatures above.

```python
from Orange.data import Table
from Orange.distance import Euclidean, Manhattan

iris = Table("iris")
rows = Euclidean(iris, normalize=True)        # shape: (len(iris), len(iris)); axis == 1
cols = Manhattan(iris, axis=0)                # feature distances; axis == 0

train, test = iris[:100], iris[100:]
metric = Euclidean(normalize=True).fit(train) # fit stats for normalization/missing handling
within_test = metric(test[:3])                # pairwise distances among test rows
train_to_one = metric(train, test[0])         # distances from train rows to one test row
```

Distance caveats to preserve:

- `Euclidean` and `Manhattan` optionally normalize numeric features; normalized distances scale numeric and discrete contributions more comparably.
- Missing values are handled by expected-distance formulas for metrics that support them. If a metric does not support missing values, widgets may impute and warn.
- `Jaccard` treats attributes as set-membership indicators; in `OWDistances`, non-binary features are ignored or rejected for dense tables.
- Correlation distances and `Mahalanobis` do not handle missing/discrete data in the same way as Euclidean/Manhattan.
- `Mahalanobis` is intentionally guarded in `OWDistances`: up to 1000 rows for column distances and up to 1000 columns for row distances; the widget also rejects more than 20,000 compared items.
- Sparse support is metric-dependent; `OWDistances` disables or errors on dense-only metrics for sparse tables.

`DistMatrix` facts:

- `DistMatrix(data, row_items=None, col_items=None, axis=1)` extends `numpy.ndarray`.
- `row_items` and `col_items` identify matrix rows/columns; for row distances, `row_items` is usually the source `Table`.
- `.axis == 1` means distances between table rows; `.axis == 0` means distances between variables/columns.
- `.submatrix(...)` preserves row/column item metadata where possible.
- `.from_file(...)` reads `.dst`/`.xlsx` distance matrices, but generic file mechanics should stay with `data-preparation` unless the task is specifically about downstream distance visualization.

## Statistics helpers behind plots

Important statistics constructors verified by introspection:

```python
from Orange.statistics.basic_stats import BasicStats, DomainBasicStats
from Orange.statistics import distribution, contingency

BasicStats(dat=None, variable=None)
DomainBasicStats(data, include_metas=False, compute_variance=False)
distribution.Discrete(dat, variable=None, unknowns=None)
distribution.Continuous(dat, variable=None, unknowns=None)
contingency.Discrete(dat, col_variable=None, row_variable=None,
                     row_unknowns=None, col_unknowns=None, unknowns=None)
contingency.Continuous(dat, col_variable=None, row_variable=None,
                       col_unknowns=None, row_unknowns=None, unknowns=None)
```

Use these when explaining plot internals or reproducing plot summaries:

- `DomainBasicStats(data, compute_variance=True)` gives per-variable min/max/mean/variance/missing counts used by numeric plot diagnostics.
- `distribution.Discrete(data, var)` and `distribution.Continuous(data, var)` carry value counts, unknowns, normalization, sampling, and `modus`/min/max behavior.
- `contingency.Discrete` and `contingency.Continuous` back grouped categorical/numeric visualizations such as Sieve, Mosaic, Correspondence Analysis, Distributions, and Box Plot.
- The widgets usually call storage-level `_compute_*` methods for efficient summaries; do not reimplement these with manual row loops unless debugging.

## Clustering APIs

Verified signatures:

```python
from Orange.clustering import KMeans, DBSCAN, HierarchicalClustering, Louvain

KMeans(n_clusters=8, init='k-means++', n_init=10, max_iter=300,
       tol=0.0001, random_state=None, preprocessors=None,
       compute_silhouette_score=None)
DBSCAN(eps=0.5, min_samples=5, metric='euclidean', algorithm='auto',
       leaf_size=30, p=None, preprocessors=None)
HierarchicalClustering(n_clusters=2, linkage='average')
Louvain(k_neighbors=30, metric='l2', resolution=1.0,
        random_state=None, preprocessors=None)
```

Examples:

```python
from Orange.data import Table
from Orange.distance import Euclidean
from Orange.clustering import KMeans, DBSCAN, HierarchicalClustering, Louvain

iris = Table("iris")

km = KMeans(n_clusters=3, random_state=0)
labels = km(iris)                  # label array
model = km.get_model(iris)          # KMeansModel with .labels, .centroids, .k
new_labels = model(iris[:5])        # prediction path for compatible rows

db_labels = DBSCAN(eps=0.5, min_samples=2)(iris)  # noise is -1 in direct API

dist = Euclidean(iris, normalize=True)
hc_labels = HierarchicalClustering(n_clusters=3).fit_predict(dist)

lv_labels = Louvain(k_neighbors=30, metric="l2", resolution=1.0,
                    random_state=0)(iris)
```

Preserve these distinctions:

- `KMeans` and `DBSCAN` inherit Orange's `Clustering` default preprocessors: `Continuize()` and `SklImpute()` unless caller overrides `preprocessors`.
- `OWKMeans` adds an optional normalization checkbox, computes silhouettes for up to 5000 samples, and emits annotated data plus centroids.
- `OWDBSCAN` preprocesses with `Continuize`, optional `Normalize`, and `SklImpute`; it visualizes k-th-neighbor distances and emits cluster/core annotations. Widget output uses missing values for DBSCAN noise, while direct `DBSCAN` labels use `-1`.
- `HierarchicalClustering.fit_predict` expects a precomputed distance matrix; widget inputs must be symmetric, finite, and non-empty.
- `Louvain` converts tabular data to a k-nearest-neighbor graph via `matrix_to_knn_graph`, then detects graph communities. Smaller or larger `resolution` changes cluster granularity according to the widget tooltip.

## Projection APIs

Verified projection signatures:

```python
from Orange.projection import (
    PCA, SparsePCA, IncrementalPCA, TruncatedSVD, CUR,
    MDS, Isomap, LocallyLinearEmbedding, SpectralEmbedding, TSNE,
    FreeViz, RadViz, LDA,
)
from Orange.projection.som import SOM

PCA(n_components=None, copy=True, whiten=False, svd_solver='auto', tol=0.0,
    iterated_power='auto', random_state=None, preprocessors=None)
TruncatedSVD(n_components=2, algorithm='randomized', n_iter=5,
             random_state=None, tol=0.0, preprocessors=None)
MDS(n_components=2, metric=True, n_init=4, max_iter=300, eps=0.001,
    n_jobs=1, random_state=None, dissimilarity='euclidean',
    init_type='random', init_data=None, preprocessors=None)
TSNE(n_components=2, perplexity=30, learning_rate='auto',
     early_exaggeration_iter=250, early_exaggeration=12, n_iter=500,
     exaggeration=None, theta=0.5, min_num_intervals=10, ints_in_interval=1,
     initialization='pca', metric='euclidean', n_jobs=1, neighbors='auto',
     negative_gradient_method='auto', multiscale=False, callbacks=None,
     callbacks_every_iters=50, random_state=None, preprocessors=None)
FreeViz(weights=None, center=True, scale=True, dim=2, p=1, initial=None,
        maxiter=500, alpha=0.1, gravity=None, atol=1e-5, preprocessors=None)
RadViz(preprocessors=None)
SOM(dim_x, dim_y, hexagonal=False, pca_init=True, random_seed=None)
```

Pattern for `Projector` subclasses:

```python
from Orange.data import Table
from Orange.projection import PCA, RadViz

iris = Table("iris")

pca_model = PCA(n_components=2, random_state=0)(iris)
pca_table = pca_model(iris)       # Table with PC1/PC2 attributes
components = pca_model.components_

radviz_model = RadViz()(iris)
radviz_table = radviz_model(iris) # Table with radviz-x/radviz-y style coords
```

Projection caveats:

- `SklProjector` preprocesses with `Continuize()` and `SklImpute()` by default and rejects multinomial discrete attributes after preprocessing.
- `PCA` supports sparse data in this Orange wrapper, but can densify when the requested component count equals the smaller matrix dimension. `TruncatedSVD` is the safer sparse dimensionality-reduction route.
- `OWPCA` emits transformed data, original data with component metas, a components table, and a `PCA` projector. It errors on no features/no instances and warns when all components are trivial.
- `MDS` can compute from data or `DistMatrix`; precomputed matrices must be symmetric and at least 2x2. `init_type='PCA'` uses Torgerson initialization.
- `TSNE` requires dense data in direct API (`compute_affinities` raises on sparse). `OWtSNE` disables normalization for sparse data, supports precomputed distances only with spectral initialization, and often benefits from PCA preprocessing for many features.
- `FreeViz` is class/target-aware. The widget requires one target variable, at least two unique target values, at least two features, dense data, no more features than instances, non-constant data, and at most 10,000 valid rows; non-binary categorical features are removed.
- `RadViz` rejects categorical variables with more than two values; use continuization or choose numeric/binary features.
- `OWLinearProjection` offers circular, LDA, and PCA placements. Its LDA placement is disabled unless the target is categorical with enough distinct values; route learner/model work elsewhere.
- `SOM.prepare_data(X)` removes rows with non-finite values and scales numeric columns. `OWSOM` ignores categorical variables, needs numeric columns and at least two valid rows, and warns on single numeric column or missing values.

## Widget utility APIs worth recognizing

- `OWDataProjectionWidget` is the shared base for scatter-like 2D data projection widgets. It defines Data/Data Subset inputs and Selected Data/Annotated Data outputs, manages `attr_color`, `attr_label`, `attr_shape`, `attr_size`, `selection`, and `DomainContextHandler` settings.
- `OWAnchorProjectionWidget` adds draggable anchors and a Components output; it rejects sparse data, no valid data, and fewer than two rows.
- `VizRankMixin`-based widgets can suggest informative feature pairs/subsets; these suggestions usually require a color variable and non-sparse data.
- `WidgetPreview(WidgetClass).run(table_or_matrix)` is the small native preview path for manual/offscreen GUI smoke checks when a widget must be instantiated.
