# Tools Workflow Recipes

Use these recipes for `squidpy.tl` helpers that annotate spatial windows or create design matrices for distance-to-anchor analysis. They assume the input object already has valid observations, coordinates, expression values, and optional library/covariate columns; route structural repair to `datasets-and-io`.

## Choose the Helper

| Goal | Primary API | Main input keys | Main output |
| --- | --- | --- | --- |
| Assign each observation to one non-overlapping spatial window | `sq.tl.sliding_window(..., overlap=0)` | `adata.obs[coord_columns]` or `adata.obsm[spatial_key]`; optional `adata.obs[library_key]` | `adata.obs[sliding_window_key]` categorical plus coordinate columns |
| Mark membership in overlapping spatial windows | `sq.tl.sliding_window(..., overlap>0)` | Same as non-overlapping windows | One boolean `adata.obs` column per window, named from `sliding_window_key` |
| Build distances to anchor cell types or regions | `sq.tl.var_by_distance(..., cluster_key=...)` | `adata.obs[cluster_key]`, `adata.obsm['spatial']`, optional `adata.obs[library_key]` | `adata.obsm[design_matrix_key]` pandas DataFrame |
| Include donor/batch/model terms in distance analysis | `sq.tl.var_by_distance(..., covariates=...)` | Covariate columns in `adata.obs` | Covariate columns copied into the design matrix |
| Plot distance trends | `sq.pl.var_by_distance(...)` | Existing `adata.obsm[design_matrix_key]` plus selected variables | Matplotlib axes or saved figure; route formatting to `visualization` |

## Spatial Windows

Use `sliding_window` when a downstream analysis needs spatially contiguous observation groups rather than a neighbor graph.

```python
import squidpy as sq

window_df = sq.tl.sliding_window(
    adata,
    library_key="sample",
    window_size=300,
    overlap=0,
    coord_columns=("globalX", "globalY"),
    sliding_window_key="spatial_window",
    drop_partial_windows=False,
    copy=True,
)
```

Workflow notes:

- With `copy=True`, inspect the returned DataFrame first; with `copy=False`, the same columns are saved to `adata.obs`.
- `coord_columns` names the two coordinate columns that should appear in `adata.obs`; if they are absent, Squidpy creates those output coordinate columns from the first two dimensions of `adata.obsm[spatial_key]`.
- Set `library_key` when multiple tissue sections or samples share coordinate ranges; windows are computed independently per library and names are prefixed with the library id.
- With `overlap=0`, each observation receives one categorical assignment in `sliding_window_key`.
- With `overlap>0`, each generated window becomes a boolean membership column named like `{sliding_window_key}_{library_id}_window_{i}` or `{sliding_window_key}_window_{i}`.
- `drop_partial_windows=False` keeps smaller border windows so edge observations are covered; `True` drops incomplete border windows and can leave edge observations unassigned from all overlapping-window columns.

## Distance-To-Anchor Design Matrices

Use `var_by_distance` when expression or observation values should be modeled as a function of distance to one or more anchor groups.

```python
sq.tl.var_by_distance(
    adata,
    groups=["Tumor", "Stroma"],
    cluster_key="cell_type",
    library_key="sample",
    library_id=["slide_a", "slide_b"],
    design_matrix_key="distance_design",
    covariates=["donor", "condition"],
    metric="euclidean",
)

design = adata.obsm["distance_design"]
```

Output checks:

- The design matrix index should align to `adata.obs_names` after any multi-library concatenation or multi-anchor merge.
- Each anchor gets a normalized distance column named by the anchor value and a raw distance column named `{anchor}_raw`.
- Anchor observations have raw distance `0`; normalized anchor distances are set to missing except for the nearest non-anchor scaling baseline used internally.
- If `cluster_key` is provided, the cluster annotation is retained in the design matrix.
- If `library_key` is provided, the library column is retained and distances are normalized separately within each selected library.
- If `covariates` is provided, those `.obs` columns are copied into the design matrix for downstream stratification.

## Library And Covariate Patterns

For multi-sample data, decide whether the biological question needs one model across all observations or separate distance scaling per library.

```python
sq.tl.var_by_distance(
    adata,
    groups="Epithelial",
    cluster_key="cell_type",
    library_key="library_id",
    covariates="donor",
    design_matrix_key="epithelial_distance_by_library",
)
```

Use this pattern when:

- Coordinates are meaningful only within each slide or field of view.
- Donor, batch, condition, or slide terms should be available for `sq.pl.var_by_distance(..., covariate=...)` or external modeling.
- Some libraries should be excluded through `library_id` before distances are computed.

Check after creation:

```python
design = adata.obsm["epithelial_distance_by_library"]
required = {"cell_type", "library_id", "Epithelial", "Epithelial_raw", "donor"}
missing = required.difference(design.columns)
if missing:
    raise KeyError(f"Missing design-matrix columns: {sorted(missing)}")
```

## Plot Handoff

`tools-workflows` owns creating and checking `adata.obsm[design_matrix_key]`; `visualization` owns formatting the plot.

```python
sq.pl.var_by_distance(
    adata,
    var=["GeneA", "GeneB"],
    anchor_key="Epithelial",
    design_matrix_key="epithelial_distance_by_library",
    covariate="donor",
    show_scatter=False,
    return_ax=True,
)
```

Before routing to plotting, verify:

- `design_matrix_key` exists in `adata.obsm`.
- `anchor_key` matches a distance column in that design matrix.
- `var` names are present in `adata.var_names` or `adata.obs`.
- `covariate`, if requested, is present in the design matrix; pass it to `sq.tl.var_by_distance(..., covariates=...)` first.

## Practical Guardrails

- Prefer `copy=True` during exploration so failed assumptions do not overwrite existing `.obs` or `.obsm` keys.
- Use explicit `sliding_window_key` and `design_matrix_key` values when multiple analyses will coexist.
- Keep graph-based neighborhood statistics in `graph-analysis`; a spatial window assignment is an annotation, not a graph connectivity matrix.
- Keep plot aesthetics, palettes, save paths, and axes handling in `visualization`; this sub-skill only prepares the valid design matrix for plotting.
