# Annotation API Reference

This reference covers prediction/annotation APIs only. For model discovery, download, conversion, subsetting, or marker extraction, route to `../model-management/SKILL.md`. For training a custom model, route to `../training-and-custom-models/SKILL.md`.

## `celltypist.annotate`

Verified signature for CellTypist 1.7.1:

```python
celltypist.annotate(
    filename="",
    model=None,
    transpose_input=False,
    gene_file=None,
    cell_file=None,
    mode="best match",
    p_thres=0.5,
    majority_voting=False,
    over_clustering=None,
    use_GPU=False,
    min_prop=0,
)
```

- `filename` accepts a path to a count matrix (`.csv`, `.txt`, `.tsv`, `.tab`, `.mtx`, `.mtx.gz`), a path to `.h5ad`, or an in-memory `AnnData` object.
- Table and Matrix Market inputs are treated as raw counts, normalized to 10,000 counts per cell, and log1p-transformed internally before prediction.
- `.h5ad` and in-memory `AnnData` inputs are expected to already contain log1p-normalized expression to 10,000 counts per cell in `.X`; if `.X` is invalid and `.raw.X` exists and is valid, CellTypist uses `.raw.X`.
- `model` can be a local model file path, a built-in model name, or a loaded `celltypist.models.Model`. Use a local path or loaded object for offline-safe annotation.
- `transpose_input=True` is for gene-by-cell inputs. CellTypist also warns and auto-transposes table-like inputs if it detects a likely gene-by-cell matrix.
- `.mtx`/`.mtx.gz` inputs require both `gene_file` and `cell_file`, each with one name per line matching the matrix dimensions after any requested transpose.
- `mode="best match"` assigns each cell to the class with the largest decision score/probability.
- `mode="prob match"` performs multi-label annotation: labels whose probabilities exceed `p_thres` are joined with `|`, and cells with no label over threshold are `Unassigned`.
- `majority_voting=True` runs prediction first, then refines labels by over-clustering. It is skipped for inputs with 50 or fewer cells.
- `over_clustering` may be a plain text file, an `.obs` column name for AnnData input, or a list/tuple/NumPy/Pandas vector. Its length must equal the number of input cells.
- `use_GPU=True` only affects automatic over-clustering and needs `rapids_singlecell`; CellTypist warns and falls back to CPU if it is missing.
- `min_prop` assigns a cluster to `Heterogeneous` when the dominant predicted label does not meet the required proportion.

## `Classifier`

`celltypist.classifier.Classifier` is the lower-level wrapper used by `annotate`.

```python
from celltypist.classifier import Classifier

clf = Classifier(
    filename="query_counts.csv",
    model="local_model.pkl",
    transpose=False,
    gene_file=None,
    cell_file=None,
)
predictions = clf.celltype(mode="best match", p_thres=0.5)
```

Use it when a future agent needs to separate input loading from prediction or call `over_cluster`/`majority_vote` explicitly. Its key runtime attributes after successful construction are:

- `adata`: an `AnnData` representation of the input.
- `indata`: the expression matrix used for prediction.
- `indata_genes`: the input genes after validation and any model-overlap selection.
- `indata_names`: the cell names used as prediction result index.
- `model`: the loaded `Model` wrapper.

Important `Classifier` methods:

- `celltype(mode="best match", p_thres=0.5)` returns an `AnnotationResult` and raises if no input genes overlap the model features.
- `over_cluster(resolution=None, use_GPU=False)` returns an over-clustering `Series`. It constructs a neighbor graph if needed and chooses default resolution by dataset size.
- `Classifier.majority_vote(predictions, over_clustering, min_prop=0)` appends `over_clustering` and `majority_voting` columns to an existing `AnnotationResult`.

## `AnnotationResult`

`celltypist.annotate` and `Classifier.celltype` return `celltypist.classifier.AnnotationResult`.

Core attributes:

- `predicted_labels`: a `pandas.DataFrame` indexed by input cells. It always has `predicted_labels`; after majority voting it also has `over_clustering` and `majority_voting`.
- `decision_matrix`: a `pandas.DataFrame` indexed by input cells with one column per model cell type. Values are classifier decision scores.
- `probability_matrix`: a `pandas.DataFrame` with the same shape as `decision_matrix`; values are sigmoid-transformed probabilities.
- `adata`: the `AnnData` object corresponding to the query input.
- `cell_count`: number of query cells.

Common result operations:

```python
result.summary_frequency(by="predicted_labels")
result.to_table(folder="results", prefix="query_", xlsx=False)
adata = result.to_adata(
    insert_labels=True,
    insert_conf=True,
    insert_conf_by="predicted_labels",
    insert_prob=True,
    prefix="ct_",
)
```

- `summary_frequency(by="predicted_labels")` counts labels in a selected `predicted_labels` column. Use `by="majority_voting"` only after majority voting.
- `to_table(folder, prefix="", xlsx=False)` writes `predicted_labels.csv`, `decision_matrix.csv`, and `probability_matrix.csv`, or one `annotation_result.xlsx`; the folder must already exist.
- `to_adata(...)` inserts labels, confidence, and optionally decision/probability columns into `.obs`. `insert_conf_by="majority_voting"` requires a `majority_voting` column.
- `to_plots(...)` exists on the result object but is presentation-focused; route plot planning and dotplot interpretation to `../visualization-and-results/SKILL.md`.

## Offline probability-match example

```python
import celltypist

result = celltypist.annotate(
    "query_counts.csv",
    model="local_model.pkl",
    mode="prob match",
    p_thres=0.35,
    majority_voting=True,
    over_clustering=["cluster_a", "cluster_a", "cluster_b"],
)

adata = result.to_adata(
    insert_labels=True,
    insert_conf=True,
    insert_conf_by="majority_voting",
    insert_prob=True,
    prefix="celltypist_",
)
```

Ensure the `over_clustering` vector has one entry per input cell. For inputs with 50 or fewer cells, `annotate(..., majority_voting=True)` returns raw predictions without majority-voting columns, so do not request `insert_conf_by="majority_voting"` unless the result actually contains that column.
