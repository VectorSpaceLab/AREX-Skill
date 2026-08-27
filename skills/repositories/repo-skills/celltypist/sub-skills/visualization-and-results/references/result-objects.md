# Result Objects and Exports

CellTypist annotation returns a `celltypist.classifier.AnnotationResult`. Treat it as the post-prediction container for labels, per-class scores, per-class probabilities, and the AnnData object used for prediction.

## Core Attributes

| Attribute | Shape and meaning | Typical use |
| --- | --- | --- |
| `predicted_labels` | `pandas.DataFrame` with one row per query cell. Raw predictions always include `predicted_labels`; majority-voting runs add `over_clustering` and `majority_voting`. | Review assigned labels, count labels, choose a dotplot prediction column, export labels. |
| `decision_matrix` | `pandas.DataFrame` with one row per query cell and one column per model cell type. Values are CellTypist decision scores. | Expert diagnostics or score overlays; less directly interpretable than probabilities. |
| `probability_matrix` | `pandas.DataFrame` with one row per query cell and one column per model cell type. Values are sigmoid-transformed probabilities. | Confidence checks, probability exports, probability UMAP overlays, dotplot mean color values. |
| `adata` | `AnnData` representation of the input data. For file inputs, CellTypist stores log1p-normalized expression; for AnnData inputs, it keeps the input object context. | Insert metadata with `to_adata()` or plot with Scanpy/CellTypist. |
| `cell_count` | Number of query cells, matching `predicted_labels.shape[0]`. | Quick row-count sanity check before export. |

Printing the result object summarizes the number of cells, label columns, score/probability matrix widths, and AnnData presence.

## Summaries

Use `summary_frequency(by="predicted_labels")` to count cells per raw predicted label:

```python
summary = predictions.summary_frequency(by="predicted_labels")
```

Use `summary_frequency(by="majority_voting")` only after majority voting has been run. If the `majority_voting` column is absent, route the user back to prediction generation in [annotation-workflows](../../annotation-workflows/SKILL.md) or switch the summary to raw `predicted_labels`.

The returned table has columns:

- `celltype`: predicted label values.
- `counts`: number of cells assigned to each value, sorted descending by count.

## Table and Excel Export

`AnnotationResult.to_table(folder, prefix="", xlsx=False)` writes label, decision, and probability tables. The `folder` must already exist.

```python
from pathlib import Path

outdir = Path("celltypist_outputs")
outdir.mkdir(parents=True, exist_ok=True)
predictions.to_table(folder=str(outdir), prefix="sample1_")
```

With `xlsx=False`, CellTypist writes three CSV files:

- `<prefix>predicted_labels.csv`
- `<prefix>decision_matrix.csv`
- `<prefix>probability_matrix.csv`

With `xlsx=True`, CellTypist writes one workbook:

- `<prefix>annotation_result.xlsx`

The workbook sheets are `Predicted Labels`, `Decision Matrix`, and `Probability Matrix`.

Run the bundled helper after export:

```bash
python sub-skills/visualization-and-results/scripts/result_shape_check.py \
  --folder celltypist_outputs \
  --prefix sample1_ \
  --require-predicted-labels \
  --expect-majority-voting optional
```

## AnnData Insertion

`AnnotationResult.to_adata()` returns the result AnnData after inserting selected outputs into `.obs`.

Common forms:

```python
# Labels plus raw-prediction confidence scores.
adata = predictions.to_adata(insert_labels=True, insert_conf=True)

# Labels, confidence, and probabilities; probabilities are usually easier to interpret than decision scores.
adata = predictions.to_adata(insert_labels=True, insert_conf=True, insert_prob=True)

# Prefix all inserted metadata columns to avoid collisions with existing obs columns.
adata = predictions.to_adata(insert_labels=True, insert_conf=True, insert_prob=True, prefix="ct_")
```

Inserted column rules:

- `insert_labels=True` copies every `predicted_labels` table column into `adata.obs`, with the optional `prefix` applied.
- `insert_conf=True` adds `<prefix>conf_score`.
- `insert_conf_by="predicted_labels"` sets confidence to the maximum row probability and works for raw prediction results.
- `insert_conf_by="majority_voting"` computes confidence for the majority-voted label, but requires the `majority_voting` column.
- `insert_prob=True` adds one `<prefix><cell_type>` column per probability matrix class and overrides `insert_decision=True` if both are set.
- `insert_decision=True` adds one `<prefix><cell_type>` column per decision matrix class when `insert_prob=False`.

For Excel plus AnnData workflows with prefixed confidence/probability columns:

```python
from pathlib import Path

outdir = Path("celltypist_outputs")
outdir.mkdir(parents=True, exist_ok=True)
predictions.to_table(folder=str(outdir), prefix="sample1_", xlsx=True)
adata = predictions.to_adata(insert_labels=True, insert_conf=True, insert_prob=True, prefix="ct_")
adata.write_h5ad(outdir / "sample1_with_celltypist.h5ad")
```

Then validate both artifacts:

```bash
python sub-skills/visualization-and-results/scripts/result_shape_check.py \
  --folder celltypist_outputs \
  --prefix sample1_ \
  --xlsx \
  --adata celltypist_outputs/sample1_with_celltypist.h5ad \
  --obs-prefix ct_ \
  --require-confidence \
  --expect-majority-voting optional
```

## Choosing Raw vs Majority-Voted Outputs

Use raw `predicted_labels` when:

- `majority_voting=False` was used during annotation.
- The user wants per-cell independent predictions.
- The result lacks `over_clustering` and `majority_voting` columns.

Use `majority_voting` when:

- Annotation was run with `majority_voting=True` or `Classifier.majority_vote()` was applied.
- The user wants neighborhood-aware smoothing or less crowded UMAP labels.
- The user asks for confidence scores corresponding to the majority-voted label.

Do not fabricate a `majority_voting` column. Re-run annotation with majority voting or switch downstream calls to `predicted_labels`.
