# Plotting and Dotplots

CellTypist has two post-result plotting surfaces:

- `AnnotationResult.to_plots()` writes UMAP figure files from the result AnnData.
- `celltypist.dotplot()` compares CellTypist predictions with manual labels, clusters, or another reference grouping.

## UMAP Files with `to_plots()`

`AnnotationResult.to_plots(folder, plot_probability=False, format="pdf", prefix="")` writes UMAP figures to an existing output folder.

```python
from pathlib import Path

plot_dir = Path("celltypist_plots")
plot_dir.mkdir(parents=True, exist_ok=True)
predictions.to_plots(folder=str(plot_dir), prefix="sample1_")
```

Output behavior:

- CellTypist always plots each column in `predictions.predicted_labels` over UMAP.
- Raw-only predictions produce a `<prefix>predicted_labels.<format>` figure.
- Majority-voting predictions also produce `<prefix>over_clustering.<format>` and `<prefix>majority_voting.<format>` figures.
- `plot_probability=True` additionally creates one figure per model cell type. Each figure overlays decision score and probability for that type.
- Cell type names containing `/` are sanitized to `_` in probability plot filenames.

UMAP coordinate behavior:

1. If `predictions.adata.obsm["X_umap"]` already exists, CellTypist uses it.
2. Else if `predictions.adata.obsp["connectivities"]` exists, CellTypist runs Scanpy UMAP from the existing neighbor graph.
3. Else CellTypist constructs a neighbor graph and then computes UMAP.

For large datasets, step 2 or 3 can be slow. Prefer precomputing neighbors/UMAP in Scanpy before annotation when reproducibility or runtime matters.

## Dotplot Purpose

`celltypist.dotplot()` is best when the input was an AnnData object with manual labels, clusters, or sample-derived groupings in `.obs`, and the user wants to compare those reference groups to CellTypist predictions.

```python
import celltypist

celltypist.dotplot(
    predictions,
    use_as_reference="manual_cell_type",
    use_as_prediction="predicted_labels",
    filter_prediction=0.0,
)
```

The dotplot shows:

- Rows: CellTypist prediction labels selected by `use_as_prediction`.
- Columns: reference labels/clusters selected by `use_as_reference`.
- Dot size: fraction of cells in each reference group assigned to a prediction label.
- Dot color: mean CellTypist probability score for cells in the intersection.

Use `use_as_prediction="predicted_labels"` for raw predictions. Use `use_as_prediction="majority_voting"` only when the result includes a `majority_voting` column.

## Dotplot Inputs

`predictions` must be a `celltypist.classifier.AnnotationResult`.

`use_as_reference` accepts either:

- A string column name in `predictions.adata.obs`.
- A list-like object with exactly one value per query cell.

`use_as_prediction` must be a column in `predictions.predicted_labels`. In CellTypist 1.7.1 the default is `"majority_voting"`, so raw prediction results normally need an explicit override:

```python
celltypist.dotplot(
    predictions,
    use_as_reference="manual_cell_type",
    use_as_prediction="predicted_labels",
)
```

## Order, Filter, and Display Controls

Important parameters from the installed CellTypist 1.7.1 signature:

| Parameter | Use |
| --- | --- |
| `prediction_order` | Prediction labels to display and their order. Values must exist in the selected prediction column. |
| `reference_order` | Reference labels/clusters to display and their order. Values must exist in the reference grouping. |
| `filter_prediction` | Keep only prediction labels whose maximum assignment fraction is at least this value. Must be between `0` and `1`. Ignored when `prediction_order` is provided. |
| `swap_axes` | Swap prediction/reference axes for readability. |
| `title` | Plot title. |
| `figsize` | Figure size forwarded to Scanpy's DotPlot. |
| `show`, `save`, `ax`, `return_fig` | Display, saving, axes, and object-return behavior compatible with Scanpy plotting patterns. |
| `cmap`, `vmin`, `vmax`, `colorbar_title` | Color scale for mean probabilities. |
| `dot_min`, `dot_max`, `smallest_dot`, `size_title` | Dot-size scale for fractions of cells. |

If a CellTypist error asks for a correct and comprehensive list of prediction or reference labels, compare the supplied order list with the actual categories/unique values and include every required label for that operation. For public `dotplot()` calls, subset order lists can work when every supplied label exists; missing or misspelled labels still fail during table subsetting.

## Practical Recipes

Raw predictions only:

```python
celltypist.dotplot(
    predictions,
    use_as_reference="manual_cell_type",
    use_as_prediction="predicted_labels",
    filter_prediction=0.05,
    title="Raw CellTypist labels vs manual labels",
)
```

Majority-voted predictions:

```python
celltypist.dotplot(
    predictions,
    use_as_reference="manual_cell_type",
    use_as_prediction="majority_voting",
    filter_prediction=0.05,
    title="Majority-voted CellTypist labels vs manual labels",
)
```

List-like reference labels:

```python
reference = predictions.adata.obs["leiden"].astype(str).to_numpy()
celltypist.dotplot(
    predictions,
    use_as_reference=reference,
    use_as_prediction="predicted_labels",
)
```

Return a Scanpy `DotPlot` object for additional customization:

```python
dp = celltypist.dotplot(
    predictions,
    use_as_reference="manual_cell_type",
    use_as_prediction="predicted_labels",
    return_fig=True,
)
dp.swap_axes().make_figure()
```

## Interpretation Checklist

- Confirm the reference grouping is biologically meaningful and has the same row order as the query cells.
- Confirm whether rows represent raw or majority-voted CellTypist labels.
- Treat large dots as high fractions of a reference group assigned to that prediction label.
- Treat stronger colors as higher mean probability for the assigned label, not as a count.
- Use `filter_prediction` to reduce visual clutter, but disclose the threshold because filtered labels disappear from the plot.
- When labels are crowded on UMAP, majority voting may simplify labels, but only if majority voting was actually run during annotation.
