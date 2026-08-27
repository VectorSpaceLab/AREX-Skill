# Plot catalog

Use this catalog to choose an Orange3 exploratory widget family. It focuses on widgets in `Orange.widgets.visualize` and `Orange.widgets.unsupervised` that support data exploration, projections, distance workflows, clustering, and unsupervised analysis.

## Selection map

| User goal | Use these widgets | Primary input / output contract | APIs behind the widget | Notes |
| --- | --- | --- | --- | --- |
| Inspect two variables or projected coordinates with interactive point selection | `OWScatterPlot` | `Data` + optional `Data Subset`; outputs `Selected Data`, `Annotated Data`, optional selected `Features` | `OWDataProjectionWidget`, `OWScatterPlotBase`, `ScatterPlotVizRank`, `Orange.preprocess.score.ReliefF`/`RReliefF` for ranking | Handles color/label/shape/size, jitter, regression lines, confidence ellipses, error bars. Warns when all x/y coordinates are missing. |
| Compare marginal/grouped distributions | `OWDistributions`, `OWBarPlot`, `OWBoxPlot`, `OWViolinPlot`, `OWLinePlot` | Usually `Data`; many emit selected/annotated tables | `Orange.statistics.distribution`, `Orange.statistics.contingency`, `Orange.statistics.util`, SciPy stats/KDE helpers | Choose by variable type: Distributions/Bar for categorical or binned views, Box/Violin for numeric distributions, Line Plot for series-like numeric features. |
| Explore categorical associations | `OWMosaicDisplay`, `OWSieveDiagram`, `OWCorrespondenceAnalysis` | `Data`; Correspondence emits a coordinates table | `Orange.statistics.contingency`, correspondence-analysis helpers, VizRank for Mosaic/Sieve | Needs categorical/discrete variables. Correspondence Analysis errors on empty data or no categorical data. |
| View numeric data as a heatmap and optionally cluster rows/columns | `OWHeatMap` | `Data`; outputs selected/annotated tables | `Orange.distance`, `Orange.clustering.hierarchical`, `Orange.clustering.kmeans`, heatmap utility classes | Requires numeric features; categorical features are ignored. Sparse data may be densified. Large inputs can disable clustering/ordering or be k-means compressed. |
| Compute and route pairwise distances | `OWDistances` | `Data` -> `Distances` (`Orange.misc.DistMatrix`) | `Orange.distance.Euclidean`, `Manhattan`, `Mahalanobis`, `Hamming`, `Cosine`, `PearsonR`, `SpearmanR`, `Jaccard` | Start here when downstream widgets need a `DistMatrix`. Respect sparse/large-data and metric restrictions. |
| Inspect a distance matrix numerically or visually | `OWDistanceMatrix`, `OWDistanceMap` | `Distances` -> selected data or annotated data where possible | `Orange.misc.DistMatrix`, distance-matrix item models, dendrogram helpers for Distance Map | Matrices must be non-empty; Distance Map requires symmetry. Labels come from `row_items`, variables, string metas, or enumeration. |
| Load or save precomputed distances | `OWDistanceFile`, `OWSaveDistances` | `.dst`/`.xlsx` distances in/out | `DistMatrix.from_file`, `DistMatrix.auto_symmetricized` | Use only when the task is specifically about a distance matrix file. Generic data/file mechanics remain with `data-preparation`. |
| Cluster data and annotate rows | `OWKMeans`, `OWDBSCAN`, `OWLouvainClustering` | `Data` -> `Annotated Data`; k-Means also emits `Centroids`; Louvain may emit a network if the optional network package is installed | `Orange.clustering.KMeans`, `DBSCAN`, `Louvain`, sklearn metrics, KNN graph construction | k-Means supports fixed or optimized k with silhouettes; DBSCAN has an epsilon/k-distance plot; Louvain clusters a nearest-neighbor graph and exposes PCA/normalization preprocessing. |
| Cluster an existing distance matrix | `OWHierarchicalClustering` | `Distances` + optional `Data Subset`; outputs selected/annotated data | `Orange.clustering.hierarchical.dist_matrix_linkage`, `tree_from_linkage`, `top_clusters` | Matrix must be symmetric, finite, and at least 2x2. Supports manual, height-ratio, and top-N selection methods. |
| Assess cluster quality | `OWSilhouettePlot` | `Data` or `DistMatrix`; outputs selected/annotated data with optional silhouette scores | `sklearn.metrics.silhouette_samples`, `Orange.distance.Euclidean`/`Manhattan`/`Cosine` | Needs at least two non-empty clusters. Omits rows with missing cluster assignment or undefined distances. |
| Reduce dimensions with PCA and inspect explained variance | `OWPCA` | `Data` -> transformed data, data with component metas, components table, `PCA` projector | `Orange.projection.PCA`, `Normalize`, `SliderGraph` | Requires at least one feature and one row; warns on trivial/constant components. |
| Project distances or tables to 2D | `OWMDS`, `OWtSNE`, `OWManifoldLearning` | `Data` and/or `Distances`; outputs selected/annotated projected tables | `Orange.projection.MDS`, `TSNE`, `Isomap`, `LocallyLinearEmbedding`, `SpectralEmbedding`, `PCA` preprocessing | MDS/t-SNE need valid dimensions and symmetric matrices. t-SNE is expensive and often benefits from PCA preprocessing. |
| Explore topology with a self-organizing map | `OWSOM` | `Data` -> selected/annotated data | `Orange.projection.som.SOM`, `SOM.prepare_data`, cell compute values | Requires numeric columns and at least two valid rows; ignores categorical features. Outputs `som_cell`, coordinates, and error-style annotations through computed metas. |
| Explore class/target-aware anchor projections | `OWFreeViz`, `OWRadviz`, `OWLinearProjection` | `Data` -> selected/annotated data; anchor widgets also emit `Components` | `Orange.projection.FreeViz`, `RadViz`, `PCA`, `LDA`, `OWAnchorProjectionWidget`, VizRank | These are exploratory visual projections, not learner construction. FreeViz requires a target and dense valid data; Linear Projection disables LDA when the target is unsuitable. |
| Inspect overlaps between multiple data inputs | `OWVennDiagram` | Multiple data inputs -> selected/annotated subsets | Table identity/domain utilities | Use for set-overlap exploration. Do not turn it into generic file/data preparation guidance. |

## Visualize-category boundaries

The `Orange.widgets.visualize` package also contains model-viewer widgets such as tree viewers, rule/scoring-sheet viewers, nomograms, and Pythagorean tree/forest visualizers. Route trained-model creation and evaluation to `supervised-modeling`. Use this sub-skill only when the user already has a model and asks about the widget's visualization behavior, selections, or warnings.

## Common widget output rules

- `Selected Data` is usually `None` when no visible rows/points/cells are selected.
- `Annotated Data` usually marks the current selection or groups and is safer for downstream workflows that must preserve all input rows.
- Projection widgets commonly append projection coordinates as meta variables or computed variables; do not expect their output domain to equal the input domain exactly.
- Distance widgets preserve `DistMatrix.row_items`/`col_items` when possible; downstream selection only maps back to original data when this metadata is present and compatible.
- Many widgets use `DomainContextHandler` and `ContextSetting`; a saved workflow can restore old variables or selections after a domain switch. Validate restored controls before trusting output.

## API-to-widget crosswalk

| API | Main widgets | When to use programmatically |
| --- | --- | --- |
| `Orange.distance.*` | `OWDistances`, `OWDistanceMatrix`, `OWDistanceMap`, `OWHierarchicalClustering`, `OWMDS`, `OWtSNE`, `OWSilhouettePlot` | Compute row/column distances, feed a precomputed `DistMatrix`, or reproduce a widget's metric. |
| `Orange.clustering.KMeans` | `OWKMeans`, `OWHeatMap` k-means compression | Need labels/centroids or cluster-number sweeps without opening the widget. |
| `Orange.clustering.DBSCAN` | `OWDBSCAN` | Need density-based labels/noise after choosing `eps` and `min_samples`. |
| `Orange.clustering.HierarchicalClustering` and `Orange.clustering.hierarchical` helpers | `OWHierarchicalClustering`, `OWHeatMap` clustering | Need dendrogram/cut labels from a precomputed distance matrix. |
| `Orange.clustering.Louvain` | `OWLouvainClustering` | Need community labels from a nearest-neighbor graph or tabular data converted to one. |
| `Orange.projection.PCA` / `TruncatedSVD` | `OWPCA`, `OWLinearProjection`, `OWtSNE` preprocessing, `OWLouvainClustering` preprocessing | Need reduced features or explained-variance/component tables. |
| `Orange.projection.MDS`, `TSNE`, `Isomap`, `LocallyLinearEmbedding`, `SpectralEmbedding` | `OWMDS`, `OWtSNE`, `OWManifoldLearning` | Need a 2D embedding from tables or distances. |
| `Orange.projection.FreeViz`, `RadViz`, `LDA` | `OWFreeViz`, `OWRadviz`, `OWLinearProjection` | Need target-aware/class-aware exploratory coordinates; avoid using these as supervised model training. |
| `Orange.projection.som.SOM` | `OWSOM` | Need SOM winners/cells or to explain SOM widget output. |
| `Orange.statistics.basic_stats`, `distribution`, `contingency` | Distributions, Bar, Box, Violin, Mosaic, Sieve, Correspondence | Need the exact summary/count objects underlying plot displays. |

## Minimal widget smoke pattern

When a GUI behavior must be checked in an installed environment, use an offscreen Qt platform and a tiny built-in table or distance matrix:

```python
from Orange.data import Table
from Orange.distance import Euclidean
from Orange.widgets.utils.widgetpreview import WidgetPreview
from Orange.widgets.visualize.owscatterplot import OWScatterPlot
from Orange.widgets.unsupervised.owdistancemap import OWDistanceMap

iris = Table("iris")
WidgetPreview(OWScatterPlot).run(iris)
WidgetPreview(OWDistanceMap).run(Euclidean(iris))
```

Use this as a manual smoke check only. Automated widget development/testing belongs to `widget-development`.
