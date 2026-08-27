# Troubleshooting exploration and visualization

Use this when Orange plots, projections, clustering widgets, or distance workflows produce empty output, warnings, or stale selections.

## Quick triage

1. Identify the object on the wire: `Table`, `DistMatrix`, projection table, annotated data, or selected data.
2. Check domain compatibility: variable names/types, row count, table ids, and `DistMatrix.axis`/`row_items` metadata.
3. Check validity of coordinates/features: finite numeric x/y values, at least the required rows/features, and no all-missing or all-constant data.
4. Check algorithm bounds: k/epsilon/perplexity/neighbors/distance matrix symmetry and size.
5. Check context restoration: saved selections and variables can be stale after a domain switch.

## Incompatible domains

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| A clustering model or projection model works on the training table but fails on a new table. | `ClusteringModel.__call__` and projection computed variables transform through the original/preprocessed domain. If attributes differ or transform to all undefined values, `DomainTransformationError` can be raised. | Recompute the cluster/projection on the new domain, or explicitly transform data to the original domain before applying the model. Do not reuse computed component/cluster variables across incompatible domains. |
| Distance-map/hierarchical selections no longer map to source rows. | `DistMatrix.row_items` is missing, refers to attributes (`axis=0`), or refers to a different table. | Inspect `matrix.axis`, `matrix.row_items`, and table ids. Recompute distances from the current table if selected rows must be output. |
| t-SNE or MDS reports data/distance dimension mismatch. | A `Data` input and a `Distances` input have different lengths, or the matrix was computed for another table. | Feed either matching data+matrix or only a matrix with correct `row_items`. Recompute distances after filtering rows. |
| Hierarchical Clustering subset warnings appear. | The subset does not refer to the table attached to the distance matrix. | Use a subset sliced from the same source table whose ids match `matrix.row_items`, or remove the subset signal. |

## Missing coordinates and invalid plotted points

| Symptom | Source | Recovery |
| --- | --- | --- |
| Scatter Plot warning: plot cannot be displayed because x/y is missing for all data points. | `OWScatterPlot` has `attr_x`/`attr_y` selected, but all rows have missing values for at least one selected coordinate. | Choose variables with finite values, impute/filter upstream, or switch to a plot that can summarize missing-heavy data. |
| Scatter Plot information: points with missing x/y are not displayed. | Some rows have missing coordinates. | Expect `Selected Data` to contain only visible selected rows. Use `Annotated Data` if downstream needs all rows plus marks. |
| Projection widget says no valid data/no projection. | Projection coordinates are non-finite after preprocessing or the data has too few valid rows. | Remove all-missing rows, impute, continuize, or select numeric/binary features appropriate for the projection. |
| Error bars, sizes, shapes, or labels disappear or warn about missing values. | `OWProjectionWidgetBase.get_column` filters to `valid_data` and imputes/marks undefined size or shape attributes. | Verify `attr_size`, `attr_shape`, and `attr_label` exist in the current domain and have defined values for visible rows. |

## Empty selections

Orange widgets usually emit `Selected Data = None` when no visible row/point/cell is selected.

- For scatter-like projection widgets, the selected output is built from the graph selection; if `graph.selection` is empty, selected data is `None` while annotated data can still mark no selected rows.
- For `OWBoxPlot`, no gathered filter conditions means `selected = None` and the annotated output contains no selected ids.
- For `OWDistanceMap`, an empty matrix selection sends `None` as selected data but can still send annotated table marks when row items exist.
- For `OWHierarchicalClustering`, manual/height/top-N selection that selects no leaves sends `None`; non-row matrices may not produce selected row data.
- For saved workflows, invalid saved selection indices are ignored if they exceed the new valid row count.

Recovery:

1. Confirm the current plot actually shows points/cells/leaves after filtering invalid data.
2. Clear the saved selection and reselect in the current domain.
3. Prefer `Annotated Data` when a downstream step needs all rows and can tolerate a no-selection mask.
4. If the selection should persist across data changes, preserve table ids and domain variable identities upstream.

## Invalid projections

| Projection/widget | Common failure | Recovery |
| --- | --- | --- |
| `OWPCA` / `PCA` | No features, no instances, or all/trivial components on constant data. | Use data with at least one numeric feature and one row; normalize if appropriate; filter constant columns. |
| `OWMDS` / `MDS` | Distance matrix not symmetric, matrix too small, no attributes when deriving distances from data, out-of-memory/optimization errors. | Use a symmetric at-least-2x2 matrix, reduce rows, provide valid attributes, or lower iterations/refresh. |
| `OWtSNE` / `TSNE` | Fewer than 2 rows or attributes, constant/no-valid data, dimension mismatch, non-symmetric/tiny distance matrix, sparse normalization unsupported. | For sparse input, disable normalization; for many features, enable PCA preprocessing; for precomputed distances, use spectral initialization and matching dimensions. |
| `OWFreeViz` / `FreeViz` | No target, multiple targets, fewer than two unique target values, fewer than two features, features exceed instances, constant data, dense-only requirement, too many valid rows. | Provide one suitable target, reduce feature count, filter/normalize upstream, avoid sparse inputs, and sample if more than 10,000 valid rows. |
| `OWRadviz` / `RadViz` | Categorical attributes with more than two values are unsupported. | Use numeric/binary features or continuize upstream. |
| `OWLinearProjection` | No continuous features; LDA placement disabled for no/continuous/low-cardinality target. | Use continuous features; use circular/PCA placement if the target is unsuitable for LDA. |
| `OWSOM` / `SOM` | No numeric columns, fewer than two rows without missing values, categorical variables ignored, single numeric column warning. | Keep/derive numeric columns, filter or impute rows with undefined values, and treat categorical coloring as annotation only. |
| `OWManifoldLearning` | Algorithm-specific neighbor/perplexity/metric errors. | Match method parameters to row count; prefer PCA/MDS for small data and t-SNE/Isomap/LLE/Spectral only when their assumptions fit. |

## Clustering parameter bounds

| Clusterer/widget | Bound or guard | Recovery |
| --- | --- | --- |
| `OWKMeans` | k is limited by the number of unique data instances; optimization range also requires enough rows. Fixed k spinner is 2-30; optimize range keeps `k_from < k_to`. | Set k/range below the unique-row count, remove duplicate/all-missing rows, or use DBSCAN/hierarchical clustering. |
| `KMeans` API | scikit-learn parameters are passed through; Orange preprocesses with `Continuize` and `SklImpute` unless overridden. | Set `random_state` for reproducibility; use `preprocessors=[]` only after manually preparing numeric finite features. |
| `OWDBSCAN` | Needs at least two rows with any defined values and at least one feature. `min_samples` is 1-100; `eps` is at least `0.01`. | Use the k-distance plot to choose `eps`; increase/decrease `min_samples` according to density. Noise is marked missing in widget output but `-1` in direct API labels. |
| `OWLouvainClustering` | Requires features; `k_neighbors` is 1-200; PCA preprocessing maxes at 50 components in the widget. | Lower `k_neighbors` for small data, enable PCA for high-dimensional data, and adjust `resolution` to change cluster granularity. |
| `OWHierarchicalClustering` | Input distance matrix must be symmetric, finite, and non-empty/at least 2x2. Top-N selection is bounded by widget spinbox. | Recompute distances with a symmetric metric, remove NaN/inf distances, or use a row-based `DistMatrix` if selected data is needed. |
| `OWSilhouettePlot` | Needs at least two non-empty clusters; singleton-only clusters are rejected; distance computation can raise memory/value errors. | Ensure cluster variable has at least two populated groups, reduce rows, and use Euclidean/Manhattan/Cosine or a symmetric precomputed matrix. |

## Sparse and large-data caveats

- `OWDistances` disables metrics without sparse support and warns when categorical/non-binary features are ignored. Dense-only metric + sparse data emits an error.
- `OWDistances` rejects more than 20,000 compared rows/columns and guards `Mahalanobis` at 1000 rows/columns depending on axis.
- `OWHeatMap` ignores categorical features, may densify sparse data with a memory warning, and uses size guards for clustering/ordered clustering and k-means merging.
- `OWKMeans` disables normalization on sparse data and warns that sparse data cannot be normalized.
- `OWtSNE` does not normalize sparse data; direct `TSNE.compute_affinities` rejects sparse matrices. Use `TruncatedSVD`/PCA-style preprocessing or densify only if safe.
- `OWFreeViz` and `OWAnchorProjectionWidget` are dense-only.
- Projection and distance widgets can allocate O(n²) matrices. For large n, sample rows, use PCA/SVD first, or avoid all-pairs distance views.

## Widget context staleness

Many visualization widgets store variables, selections, annotations, and display settings with `DomainContextHandler`, `ContextSetting`, or a custom context handler. Staleness appears when a saved workflow is opened on a different domain or when a table is replaced after variables are renamed or moved between attributes/classes/metas.

Typical signs:

- A control shows a variable name that no longer exists or has a different type.
- A saved selection has no effect, selects unexpected rows, or is silently ignored.
- Distance Matrix restores labels/selection only if shape, symmetry, and annotation options match.
- Hierarchical Clustering attempts to restore a manual selection only when linkage/state still match the current tree.
- Scatter/MDS/t-SNE contexts restore color/label/shape/size options that may be invalid for a new domain.

Recovery:

1. Close/reopen the widget context by disconnecting data, reconnecting the current table, and reselecting variables.
2. Clear saved selection fields in the workflow/widget settings if stale selection must not persist.
3. In Canvas-level debugging, use the Orange CLI clear-settings options only when appropriate for the whole user environment (for example `orange-canvas --clear-widget-settings` or broader clearing flags shown by `orange-canvas --help`).
4. For programmatic smoke tests, construct a fresh widget instance rather than reusing one after domain changes.
5. When producing a reusable workflow, document the expected domain variables and whether row ids must remain stable.

## Distance matrix validity checklist

Before sending a matrix to Distance Map, Hierarchical Clustering, MDS, t-SNE, or Silhouette Plot:

```python
assert matrix.ndim == 2
assert matrix.shape[0] == matrix.shape[1]
assert len(matrix) >= 2
assert matrix.is_symmetric()
assert np.all(np.isfinite(matrix))
```

Then check metadata:

- `matrix.axis == 1`: matrix rows correspond to data instances.
- `matrix.axis == 0`: matrix rows correspond to variables/features; selected data outputs may become attribute labels rather than table rows.
- `matrix.row_items is not None`: downstream widgets can label rows and often map selections back to data.
- If a separate `Data` signal is present, `len(data) == len(matrix)` must hold.
