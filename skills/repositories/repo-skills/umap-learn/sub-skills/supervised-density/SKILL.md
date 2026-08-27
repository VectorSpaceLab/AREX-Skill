---
name: supervised-density
description: "Supervised, semi-supervised, densMAP, clustering, and outlier
  workflows for umap-learn."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# supervised-density

Use this sub-skill when labels, partial labels, density preservation, or
clustering/outlier interpretation are central to a `umap.UMAP` task.

## Route here for

- Supervised `UMAP.fit(X, y=...)` or `fit_transform(X, y=...)`.
- Semi-supervised class labels, including the categorical `-1` unlabeled
  convention.
- Choosing `target_metric`, `target_weight`, `target_n_neighbors`, and
  `target_metric_kwds`.
- `densmap=True`, `dens_lambda`, `dens_frac`, `dens_var_shift`, and
  `output_dens=True`.
- UMAP-assisted KMeans/HDBSCAN clustering, LOF-style outlier review, and
  exploratory-analysis caveats.

## Route elsewhere

- Base estimator mechanics, transform/inverse/update, sparse/precomputed data,
  and general distance metrics: use the `core-embedding` sub-skill.
- Plot rendering and `umap.plot`: use the `plotting-diagnostics` sub-skill.
- Aligned multi-slice embeddings: use the `aligned-composition` sub-skill.
- TensorFlow/Keras ParametricUMAP: use the `parametric-umap` sub-skill.

## Read first

- [Supervised and density workflows](references/workflows.md)
- [Target and densMAP API reference](references/api-reference.md)
- [Troubleshooting](references/troubleshooting.md)

## Safe smoke helper

Run the bundled helper from this sub-skill directory for a no-network toy-data
check:

```bash
python scripts/supervised_density_smoke.py --help
```

Use options such as `--partial-label-fraction`, `--densmap`, `--output-dens`,
`--cluster-method kmeans`, and `--outlier-check` to exercise harder cases.

## Operating cautions

- Labels guide topology; they do not guarantee better scientific structure.
- densMAP preserves relative local-density information more than standard UMAP,
  but costs extra runtime and has transform/inverse limitations.
- Clusters and outliers from a UMAP embedding are exploratory until validated
  against labels, stability, original-space neighbors, or domain evidence.
