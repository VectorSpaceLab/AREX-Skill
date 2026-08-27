---
name: tools-workflows
description: "Use Squidpy tool-layer workflows for sliding windows,
  distance-to-anchor design matrices, and plotting handoffs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Tools Workflows

Use this sub-skill when a Squidpy task needs `squidpy.tl` helper workflows for spatial windows or distance-to-anchor design matrices. Keep plotting details routed to `visualization` once the design matrix exists.

## Use This For

- Assigning observations to spatial windows with `sq.tl.sliding_window`.
- Building normalized distance-to-anchor design matrices with `sq.tl.var_by_distance`.
- Preserving library, donor, batch, or other covariates in design matrices for downstream models and plots.
- Handing a valid design matrix to `sq.pl.var_by_distance` without duplicating plot-formatting guidance.

## Route Elsewhere

- Use `datasets-and-io` for AnnData/SpatialData structure, coordinate validation, readers, and missing metadata repair.
- Use `graph-analysis` for spatial neighbor graphs, graph statistics, ligand-receptor, Ripley, Moran/Geary, Sepal, niche, or graph masking workflows.
- Use `visualization` for `sq.pl.var_by_distance` layout, palettes, axes, saving, or other plot-formatting choices after `adata.obsm[design_matrix_key]` is valid.
- Use `image-analysis` or `experimental-imaging` for image containers, segmentation, tissue tiling, QC, staining, or SpatialData image workflows.

## Start Here

1. Read `references/tools-workflows.md` for workflow recipes and output checks.
2. Read `references/api-reference.md` for focused signatures, parameters, and storage keys.
3. Read `references/troubleshooting.md` for coordinate columns, anchors, libraries, covariates, partial windows, and plot handoff failures.
4. Run `scripts/var_by_distance_smoke.py --help` to inspect the bundled no-download smoke check, then run it with `--quiet` for a compact installation/API check.

## Minimal Pattern

```python
import squidpy as sq

sq.tl.sliding_window(
    adata,
    window_size=100,
    overlap=0,
    coord_columns=("globalX", "globalY"),
    sliding_window_key="sliding_window_assignment",
)

sq.tl.var_by_distance(
    adata,
    groups="Tumor",
    cluster_key="cell_type",
    library_key="sample",
    covariates="donor",
    design_matrix_key="design_matrix",
)

sq.pl.var_by_distance(
    adata,
    var="GeneA",
    anchor_key="Tumor",
    design_matrix_key="design_matrix",
    covariate="donor",
)
```

Confirm storage keys before downstream use: `sliding_window` writes columns to `adata.obs` when `copy=False`, and `var_by_distance` writes a pandas design matrix to `adata.obsm[design_matrix_key]` when `copy=False`.
