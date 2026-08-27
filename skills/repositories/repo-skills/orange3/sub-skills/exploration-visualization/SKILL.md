---
name: exploration-visualization
description: "Routes Orange3 exploratory plots, distance matrices, projections,
  clustering, statistics, and unsupervised widgets."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# exploration-visualization

Use this sub-skill when an existing Orange table or distance matrix must be explored with Orange3 plots, projections, distances, clustering, statistics, or unsupervised widgets.

## Route here for

- Choosing and wiring `Orange.widgets.visualize` exploratory widgets such as Scatter Plot, Box Plot, Distributions, Violin Plot, Heat Map, Sieve/Mosaic, Silhouette Plot, FreeViz, Linear Projection, and Radviz.
- Choosing and wiring `Orange.widgets.unsupervised` widgets such as Distances, Distance Matrix/Map, k-Means, DBSCAN, Louvain, Hierarchical Clustering, PCA, MDS, t-SNE, Manifold Learning, SOM, and Correspondence Analysis.
- Programmatic use of `Orange.distance`, `Orange.clustering`, `Orange.projection`, and `Orange.statistics` for exploratory analysis.
- Explaining `Orange.misc.DistMatrix` flow between distance, clustering, map, MDS, t-SNE, and silhouette widgets.
- Diagnosing plot/projection/clustering failures caused by invalid coordinates, stale context, sparse inputs, distance matrix shape/symmetry, or clustering bounds.

## Route elsewhere

- Loading, saving, SQL, `Table`/`Domain` construction, file formats, and generic data preparation: use `data-preparation`.
- Supervised learner/model construction, prediction, scoring, or evaluation: use `supervised-modeling`.
- Building custom Orange widgets, Canvas workflow internals, widget catalog tooling, or GUI framework tests: use `widget-development`.
- Trained-model visualization widgets such as tree viewers, nomograms, rule viewers, scoring-sheet viewers, or Pythagorean tree/forest unless the task is only to inspect an already-created model; create or evaluate the model elsewhere first.

## Read first

- [Exploration reference](references/exploration-reference.md) for verified distance, clustering, projection, statistics, and `DistMatrix` API patterns.
- [Plot catalog](references/plot-catalog.md) for widget selection, inputs/outputs, and the APIs behind each plot or unsupervised widget family.
- [Troubleshooting](references/troubleshooting.md) for incompatible domains, missing coordinates, empty selections, invalid projections, clustering bounds, sparse/large-data caveats, and widget context staleness.

## Typical workflow

1. Start from an already-prepared `Orange.data.Table` or `Orange.misc.DistMatrix`; do not re-own file/SQL loading here.
2. Decide whether the user needs a plot, a distance matrix, a clustering annotation, a low-dimensional projection, or a cluster-quality diagnostic.
3. For code, use the verified APIs in `references/exploration-reference.md`; for GUI work, use the widget catalog and preserve each widget's input/output contract.
4. Before trusting selections or downstream outputs, check whether the widget has valid coordinates/projections and whether the current context was restored from a compatible domain.

## Bundled scripts

No helper script is bundled for this sub-skill. The selected repository evidence did not provide a small visualization helper that improves on the distilled references. For GUI smoke checks, instantiate native widgets or `WidgetPreview` from the active Orange environment rather than adding a copied build/release helper.

## Evidence distilled

This sub-skill distills Orange3 3.41.0.dev exploratory behavior for `Orange.distance`, `Orange.clustering`, `Orange.projection`, `Orange.statistics`, `Orange.widgets.visualize`, and `Orange.widgets.unsupervised`. Runtime guidance is self-contained and relies on installed Orange APIs plus the bundled references here.
