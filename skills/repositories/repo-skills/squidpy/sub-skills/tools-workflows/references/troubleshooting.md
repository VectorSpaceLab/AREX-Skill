# Tools Workflow Troubleshooting

Use this guide when `sliding_window`, `var_by_distance`, or the `sq.pl.var_by_distance` handoff fails.

## Coordinate Columns Are Missing Or Wrong

Symptoms:

- `sliding_window` raises that coordinates were not found.
- Window assignments look transposed, shifted, or grouped by the wrong coordinate frame.
- A workflow uses global tissue coordinates but only `.obsm['spatial']` exists.

Fixes:

- If global coordinates are in `.obs`, pass their exact names with `coord_columns=("globalX", "globalY")` or the dataset-specific equivalent.
- If coordinates live in `.obsm`, pass `spatial_key` and keep `coord_columns` as the output names you want in the returned/saved window table.
- Validate coordinate dtype and missing values before windowing; route deeper object repair to `datasets-and-io`.
- For `var_by_distance`, keep usable coordinates in `adata.obsm['spatial']` for safest behavior because the current coordinate extraction path expects that key internally.

## Window Size, Overlap, Or Partial Windows Fail

Symptoms:

- `Window size must be larger than 0.`
- `Overlap must be non-negative.`
- `Overlap must be less than the window size.`
- Edge observations are not assigned as expected.

Fixes:

- Use a positive `window_size` and ensure `0 <= overlap < window_size`.
- Start with `copy=True` and inspect the returned DataFrame before writing to `.obs`.
- Keep `drop_partial_windows=False` when every border observation should be covered by clipped border windows.
- Use `drop_partial_windows=True` only when incomplete edge windows should be discarded.
- Remember that `overlap=0` creates a single categorical assignment column, while `overlap>0` creates many boolean membership columns.

## Multi-Library Windows Or Distances Look Mixed

Symptoms:

- Windows span multiple tissue sections.
- Distance normalization is dominated by a large slide or field of view.
- `library id ... not in ...` is raised.

Fixes:

- Pass `library_key` whenever coordinates are only comparable within a sample, slide, library, or field of view.
- Check `adata.obs[library_key].unique()` before passing `library_id`; every selected id must exist.
- For `sliding_window`, expect library-prefixed window names when `library_key` is used.
- For `var_by_distance`, distances are computed and normalized per selected library when `library_key` is provided.
- If a library has no anchor observations for a `cluster_key` group, Squidpy skips that library/anchor combination; check design-matrix columns and row coverage after creation.

## Anchor Groups Are Missing Or Ambiguous

Symptoms:

- Design matrix is empty, missing an anchor column, or lacks rows for an expected slide.
- Anchor raw-distance column does not show zeros for expected anchor cells.
- Multiple anchor labels produce unexpected column merges.

Fixes:

- Confirm `cluster_key` exists in `adata.obs` and contains each requested value in `groups`.
- Use the exact category label from `adata.obs[cluster_key]`; category capitalization and whitespace must match.
- When passing custom coordinates as `groups`, use a one-dimensional coordinate-like list/array for one anchor point; multi-dimensional arrays are rejected.
- After creation, verify `{anchor}` and `{anchor}_raw` columns for every requested anchor.
- For multiple libraries and multiple anchors, inspect `design.index.equals(adata.obs.index)` and expected non-null values per library.

## Covariates Are Missing From The Plot

Symptoms:

- `sq.pl.var_by_distance(..., covariate="donor")` cannot group lines.
- Donor, batch, or condition terms are absent from the design matrix.

Fixes:

- Pass covariates during design-matrix creation, not only during plotting:

```python
sq.tl.var_by_distance(
    adata,
    groups="Epithelial",
    cluster_key="cell_type",
    library_key="sample",
    covariates=["donor", "condition"],
    design_matrix_key="distance_design",
)
```

- Verify every covariate exists in `adata.obs` before calling `var_by_distance`.
- Use categorical dtype for covariates that should produce separate regression lines.
- Avoid `stack_vars=True` with `covariate`; the plotting function treats that combination as invalid.

## Design Matrix Key Mismatch

Symptoms:

- `KeyError` when plotting with `design_matrix_key`.
- Plot uses stale distances from a previous run.
- Expected anchor or covariate columns are missing.

Fixes:

- Use the same `design_matrix_key` in `sq.tl.var_by_distance` and `sq.pl.var_by_distance`.
- Give each analysis a descriptive key when comparing anchors, libraries, or covariate sets.
- Remove or overwrite stale `.obsm` keys intentionally; `copy=True` is safer while experimenting.
- Validate the design matrix before plotting:

```python
design = adata.obsm["distance_design"]
required = {"Epithelial", "Epithelial_raw", "donor"}
missing = required.difference(design.columns)
if missing:
    raise KeyError(sorted(missing))
```

## Plot Handoff Fails

Symptoms:

- `Variable ... not found in adata.var or adata.obs.`
- The plot cannot find `anchor_key`.
- Plot styling, palette, axis, or save behavior is wrong.

Fixes:

- Confirm `var` names are genes in `adata.var_names` or observation columns in `adata.obs`.
- Confirm `anchor_key` is the normalized distance column in `adata.obsm[design_matrix_key]`, not the raw-distance column unless intentionally plotting raw distance.
- Confirm `color`, if supplied, is available in the design matrix or compatible with the plotting call.
- Route plot-only questions to `visualization` after the design matrix passes input checks.

## Separate Distance Models Per Donor And Library

For a donor-stratified, multi-library task, keep libraries in the design matrix and copy donor covariates explicitly:

```python
sq.tl.var_by_distance(
    adata,
    groups="Tumor",
    cluster_key="cell_type",
    library_key="library_id",
    covariates="donor",
    design_matrix_key="tumor_distance_by_library",
)
```

Then check each donor/library group before plotting or external modeling:

```python
design = adata.obsm["tumor_distance_by_library"]
summary = design.groupby(["library_id", "donor"], observed=True)["Tumor"].count()
if summary.empty:
    raise ValueError("No donor/library groups have tumor-distance values")
```

## Global Coordinate Columns Instead Of `.obsm['spatial']`

For windowing, direct global columns are supported:

```python
sq.tl.sliding_window(
    adata,
    coord_columns=("global_x", "global_y"),
    window_size=250,
    sliding_window_key="global_window",
)
```

For distance-to-anchor analysis, also mirror the intended coordinate frame into `adata.obsm['spatial']` before calling `var_by_distance` when your source coordinates are not already there:

```python
adata.obsm["spatial"] = adata.obs[["global_x", "global_y"]].to_numpy()
sq.tl.var_by_distance(adata, groups="Tumor", cluster_key="cell_type")
```
