---
name: annotation-workflows
description: "Run CellTypist prediction and annotation workflows from Python or
  CLI for tables, Matrix Market, h5ad, and AnnData."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# CellTypist Annotation Workflows

Use this sub-skill when a task is about assigning CellTypist labels to query cells, validating annotation inputs, exporting prediction tables, or choosing between Python and CLI prediction workflows.

## Route quickly

- Use [API reference](references/api-reference.md) for `celltypist.annotate`, `Classifier`, `AnnotationResult`, best-match vs probability-match modes, majority voting, and result shapes.
- Use [data formats](references/data-formats.md) before running annotation on count tables, Matrix Market files, `.h5ad`, or in-memory `AnnData`.
- Use [CLI reference](references/cli-reference.md) when the user wants `celltypist --indata ...` commands, output flags, or batchable shell patterns.
- Use [troubleshooting](references/troubleshooting.md) for missing `.mtx` sidecar files, transposed matrices, normalization errors, model-feature mismatches, output-folder failures, majority-voting skips, GPU fallback, and cache/network surprises.
- Run [annotation_smoke.py](scripts/annotation_smoke.py) to create a tiny local model and query table in a temporary directory, annotate without network downloads, and verify prediction/result-table shapes.

## Stay in scope

- Keep model download, cache inventory, model conversion, model subsetting, and marker extraction in [model-management](../model-management/SKILL.md).
- Keep custom model training and downsampling strategy in [training-and-custom-models](../training-and-custom-models/SKILL.md); this sub-skill only uses a tiny synthetic model for smoke checks.
- Keep dotplots, UMAP figures, presentation plots, and result interpretation in [visualization-and-results](../visualization-and-results/SKILL.md).

## Default annotation pattern

Prefer an explicit local model path or loaded `Model` object when the user needs offline behavior. Leaving `model=None` or using built-in model names can consult CellTypist's model cache and may require network access if the cache is empty.

```python
import celltypist

predictions = celltypist.annotate(
    "query_counts.csv",
    model="local_model.pkl",
    mode="best match",
)

predictions.to_table(folder="results", prefix="query_")
adata = predictions.to_adata(insert_labels=True, insert_conf=True, insert_prob=True)
```

For CLI workflows, create the output directory first and use CLI mode names with underscores:

```bash
mkdir -p results
celltypist --indata query_counts.csv --model local_model.pkl --outdir results --prefix query_ --quiet
```
