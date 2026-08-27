# Tools API Reference

Focused reference for the Squidpy tool-layer helpers owned by this sub-skill.

## `sq.tl.sliding_window`

Signature:

```python
sq.tl.sliding_window(
    adata,
    library_key=None,
    window_size=None,
    overlap=0,
    coord_columns=("globalX", "globalY"),
    sliding_window_key="sliding_window_assignment",
    spatial_key="spatial",
    drop_partial_windows=False,
    copy=False,
    *,
    table_key=None,
)
```

Purpose: divide observations into regularly shaped spatial windows.

Inputs:

- `adata`: `AnnData` or `SpatialData`. For `SpatialData`, pass `table_key` when the table is ambiguous.
- `coord_columns`: two column names in `adata.obs` to use as x/y coordinates; if missing, Squidpy falls back to the first two columns of `adata.obsm[spatial_key]` and uses these names in the returned/saved DataFrame.
- `library_key`: optional `.obs` column used to compute separate windows per library, slide, or field of view.
- `window_size`: positive integer side length. If `None`, Squidpy infers a size from the coordinate range.
- `overlap`: non-negative integer overlap. It must be smaller than `window_size`.
- `drop_partial_windows`: when `False`, border windows are clipped to cover the coordinate extent; when `True`, incomplete border windows are dropped.
- `sliding_window_key`: base output column name.
- `copy`: when `True`, returns a DataFrame instead of modifying the object.

Outputs:

- With `copy=True`, returns a pandas DataFrame indexed like `adata.obs`.
- With `copy=False`, writes each output column to `adata.obs` and returns `None`.
- With `overlap=0`, output includes one ordered categorical assignment column named `sliding_window_key`.
- With `overlap>0`, output includes one boolean membership column per window; the base assignment column is not created.
- Output always includes the coordinate columns named by `coord_columns`.

Common checks:

```python
windows = sq.tl.sliding_window(adata, window_size=100, copy=True)
assert windows.index.equals(adata.obs.index)
assert {"globalX", "globalY"}.issubset(windows.columns)
```

## `sq.tl.var_by_distance`

Signature:

```python
sq.tl.var_by_distance(
    adata,
    groups,
    cluster_key=None,
    library_key=None,
    library_id=None,
    design_matrix_key="design_matrix",
    covariates=None,
    metric="euclidean",
    spatial_key="spatial",
    copy=False,
)
```

Purpose: build a design matrix with each observation's distance to one or more anchor groups or anchor coordinates.

Inputs:

- `adata`: `AnnData` with expression/observation data and spatial coordinates.
- `groups`: a single anchor label, a list of anchor labels, or a one-dimensional coordinate array/list used as a custom anchor.
- `cluster_key`: `.obs` column that contains anchor labels when `groups` names categories.
- `library_key`: optional `.obs` column for per-library distance calculation and normalization.
- `library_id`: optional selected library id or list of ids; values must exist in `adata.obs[library_key]`.
- `design_matrix_key`: `.obsm` key for the output DataFrame when `copy=False`.
- `covariates`: `.obs` column name or names to copy into the design matrix.
- `metric`: distance metric passed to scikit-learn's KD-tree distance machinery.
- `spatial_key`: declared coordinate key; current Squidpy behavior expects coordinates under `.obsm['spatial']` during internal coordinate extraction, so keep coordinates there for safest use.
- `copy`: when `True`, returns the design matrix instead of writing it.

Outputs:

- With `copy=True`, returns a pandas DataFrame.
- With `copy=False`, writes the DataFrame to `adata.obsm[design_matrix_key]` and returns `None`.
- Distance columns use the anchor label, with raw distances in `{anchor}_raw`.
- Distances are normalized to `[0, 1]` per library/anchor combination after raw distances are stored.
- Anchor observations have raw distance `0`; normalized distances for anchor cells can be missing because zeros are excluded from scaling and anchor membership is represented by the raw-distance column.
- Included metadata columns can include `cluster_key`, `library_key`, and any `covariates`.

Common checks:

```python
sq.tl.var_by_distance(
    adata,
    groups="Tumor",
    cluster_key="cell_type",
    library_key="sample",
    covariates=["donor"],
    design_matrix_key="tumor_distance",
)

design = adata.obsm["tumor_distance"]
assert design.index.equals(adata.obs.index)
assert {"Tumor", "Tumor_raw", "cell_type", "sample", "donor"}.issubset(design.columns)
```

## `sq.pl.var_by_distance` Handoff

Signature:

```python
sq.pl.var_by_distance(
    adata,
    var,
    anchor_key,
    design_matrix_key="design_matrix",
    stack_vars=False,
    covariate=None,
    order=5,
    show_scatter=True,
    color=None,
    line_palette=None,
    scatter_palette="viridis",
    dpi=None,
    figsize=None,
    save=None,
    title=None,
    axis_label=None,
    return_ax=None,
    regplot_kwargs={},
    scatterplot_kwargs={},
)
```

`tools-workflows` should only ensure the plot has valid inputs:

- `adata.obsm[design_matrix_key]` exists and contains `anchor_key`.
- Every `var` is in `adata.var_names` or `adata.obs`.
- `covariate`, if used, is a column in `adata.obsm[design_matrix_key]`.
- `stack_vars=True` is incompatible with `covariate`.

Route palette, axis, figure-size, return-axis, and save-path decisions to `visualization`.
