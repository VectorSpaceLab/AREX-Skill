# Troubleshooting Visualization and Results

## Output Folder Does Not Exist

Symptom:

- `to_table()` or `to_plots()` raises `FileNotFoundError` with a message that the output folder does not exist.

Cause:

- CellTypist checks `os.path.isdir(folder)` and does not create the directory for you.

Fix:

```python
from pathlib import Path

outdir = Path("celltypist_outputs")
outdir.mkdir(parents=True, exist_ok=True)
predictions.to_table(folder=str(outdir), prefix="sample1_")
```

Use the same pattern for `to_plots()`.

## Missing `majority_voting`

Symptoms:

- `predictions.to_adata(insert_conf_by="majority_voting")` raises a `KeyError` saying `majority_voting` was not found.
- `celltypist.dotplot(predictions, use_as_reference="...")` fails because its default `use_as_prediction` is `"majority_voting"`.
- The exported `predicted_labels.csv` has only `predicted_labels` and no `over_clustering` or `majority_voting` columns.

Cause:

- Annotation was run without majority voting, or a raw `AnnotationResult` was passed downstream.

Fix options:

- For raw predictions, switch downstream calls to raw labels:

```python
adata = predictions.to_adata(insert_conf=True, insert_conf_by="predicted_labels")
celltypist.dotplot(
    predictions,
    use_as_reference="manual_cell_type",
    use_as_prediction="predicted_labels",
)
```

- For majority-voted outputs, regenerate predictions with majority voting in [annotation-workflows](../../annotation-workflows/SKILL.md), then rerun export/plot steps.

Validate file exports:

```bash
python sub-skills/visualization-and-results/scripts/result_shape_check.py \
  --folder celltypist_outputs \
  --prefix sample1_ \
  --expect-majority-voting optional
```

## Confidence Column Missing or Unexpected

Symptoms:

- Saved AnnData lacks `conf_score` or `<prefix>conf_score` in `.obs`.
- A downstream workflow expects confidence scores based on majority-voted labels but sees raw-prediction confidence.

Cause:

- `insert_conf=False`, a prefix was used, or `insert_conf_by` did not match the intended label column.

Fix:

```python
adata = predictions.to_adata(
    insert_labels=True,
    insert_conf=True,
    insert_conf_by="predicted_labels",
    insert_prob=True,
    prefix="ct_",
)
```

For majority-voted confidence, first confirm `"majority_voting" in predictions.predicted_labels.columns`, then use `insert_conf_by="majority_voting"`.

Validate saved AnnData:

```bash
python sub-skills/visualization-and-results/scripts/result_shape_check.py \
  --adata celltypist_outputs/sample1_with_celltypist.h5ad \
  --obs-prefix ct_ \
  --require-confidence
```

## UMAP Plotting Is Slow

Symptoms:

- `to_plots()` runs for a long time before writing figures.
- Logs indicate CellTypist is generating UMAP coordinates or constructing a neighbor graph.

Cause:

- The result AnnData lacks `obsm["X_umap"]`; CellTypist may compute UMAP from existing connectivities or construct a neighbor graph first.

Fix options:

- If the user already has trusted Scanpy coordinates, annotate the AnnData carrying `obsm["X_umap"]` so `to_plots()` reuses them.
- If reproducibility matters, compute neighbors and UMAP explicitly in Scanpy before annotation and record the Scanpy parameters.
- If only label comparison is needed, skip UMAP files and use `celltypist.dotplot()` against a reference label column.
- Avoid `plot_probability=True` on large models unless the user needs one decision/probability figure per cell type.

## Dotplot Reference Column Not Found

Symptom:

- Dotplot raises a `KeyError` saying the reference column was not found in `predictions.adata.obs`.

Cause:

- `use_as_reference` is a string that is not an AnnData obs column, or labels were inserted under a prefix.

Fix:

```python
print(predictions.adata.obs.columns.tolist())
celltypist.dotplot(
    predictions,
    use_as_reference="manual_cell_type",
    use_as_prediction="predicted_labels",
)
```

If the reference labels are outside AnnData, pass a list-like object whose length equals `predictions.cell_count`.

## Dotplot Reference Length Mismatch

Symptom:

- Dotplot raises a `ValueError` saying the provided reference length does not match the number of cells.

Cause:

- A list-like `use_as_reference` is not aligned to the query cells.

Fix:

- Check `len(reference) == predictions.cell_count`.
- If using a Pandas Series from another AnnData object, align it to `predictions.adata.obs_names` before passing values.

## Dotplot Order Lists Fail

Symptoms:

- A CellTypist helper reports an order list is not correct or comprehensive.
- Public `dotplot()` fails while subsetting `dot_size_df` or `dot_color_df` with order values.

Cause:

- `prediction_order` or `reference_order` includes misspelled labels, omits labels required by the selected operation, or uses labels from a different column.

Fix:

```python
prediction_values = predictions.predicted_labels["predicted_labels"].astype(str).unique().tolist()
reference_values = predictions.adata.obs["manual_cell_type"].astype(str).unique().tolist()
print(sorted(prediction_values))
print(sorted(reference_values))
```

Then rebuild the order lists from those values. If the goal is clutter reduction, prefer `filter_prediction` over manually maintaining a long `prediction_order`.

## Invalid `filter_prediction`

Symptom:

- Dotplot raises `ValueError` saying `filter_prediction` must be between `0` and `1`.

Cause:

- `filter_prediction` is a fraction threshold, not a percentage.

Fix:

- Use `0.05` for 5%, `0.2` for 20%, and `0.0` for no filtering.
- Remember that `filter_prediction` only applies when `prediction_order` is not provided.

## Excel Export Cannot Be Read by the Helper

Symptoms:

- `result_shape_check.py --xlsx` reports missing Excel dependencies.
- Pandas cannot open `annotation_result.xlsx`.

Cause:

- The local environment lacks an Excel reader such as `openpyxl`, or the workbook path/prefix is wrong.

Fix options:

- Install an Excel reader in the current analysis environment.
- Re-export with `xlsx=False` and validate the three CSV files instead.
- Confirm the expected file name is `<prefix>annotation_result.xlsx`.
