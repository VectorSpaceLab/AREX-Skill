---
name: celltypist
description: "Use CellTypist for single-cell RNA-seq cell type annotation, model
  management, custom classifier training, CLI usage, and result visualization
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# CellTypist Repo Skill

Use this skill when a task involves CellTypist, automated scRNA-seq cell type annotation, CellTypist model downloads or local model pickles, `celltypist.annotate`, the `celltypist` CLI, custom CellTypist classifier training, or CellTypist result exports and plots.

## Quick Start

Install CellTypist from PyPI or conda, then verify the import and CLI:

```bash
pip install celltypist
python -c "import celltypist; print(celltypist.__version__)"
celltypist --help
```

CellTypist uses `scanpy`, `anndata`, `scikit-learn`, `pandas`, `numpy`, `openpyxl`, `click`, `requests`, and `leidenalg`. GPU paths are optional: `rapids-singlecell` affects over-clustering during majority voting, and `cuml` affects GPU logistic regression training.

## Route by Task

- Use [annotation-workflows](sub-skills/annotation-workflows/SKILL.md) for prediction with `celltypist.annotate`, count tables, Matrix Market input, `.h5ad`, in-memory `AnnData`, CLI annotation, best-match vs probability-match modes, majority voting, and table export.
- Use [model-management](sub-skills/model-management/SKILL.md) for built-in model download/cache behavior, offline model pickles, `CELLTYPIST_FOLDER`, `Model.load`, `Model.write`, marker extraction, model conversion, model subsetting, and tiny offline model fixtures.
- Use [training-and-custom-models](sub-skills/training-and-custom-models/SKILL.md) for `celltypist.train`, training matrix/label/gene validation, logistic regression vs SGD vs mini-batch, feature selection, sparse-memory settings, GPU training caveats, and `downsample_adata`.
- Use [visualization-and-results](sub-skills/visualization-and-results/SKILL.md) for `AnnotationResult` tables, Excel export, AnnData insertion, confidence scores, UMAP plot files, and `celltypist.dotplot` comparisons against manual labels or clusters.

## Common Workflows

### Annotate Query Cells

Prefer an explicit local model path when the user needs offline behavior. Built-in model names and `model=None` can consult the CellTypist model cache and may need network access if the cache is empty.

```python
import celltypist

predictions = celltypist.annotate(
    "query_counts.csv",
    model="local_model.pkl",
    mode="best match",
)
predictions.to_table(folder="results", prefix="query_")
```

For CLI usage, create the output directory first:

```bash
mkdir -p results
celltypist --indata query_counts.csv --model local_model.pkl --outdir results --prefix query_ --quiet
```

### Work Offline With Local Models

Use the model-management helpers to avoid accidental downloads:

```bash
python sub-skills/model-management/scripts/model_cache_check.py --verify-model ./local_model.pkl
python sub-skills/model-management/scripts/tiny_model_factory.py --output tiny_model.pkl --write-query-csv tiny_query.csv
```

Then pass `./local_model.pkl` or an absolute path to `Model.load()` or `celltypist.annotate()`.

### Train or Preflight Custom Models

Before expensive training, validate the matrix/label/gene shape and algorithm feasibility:

```bash
python sub-skills/training-and-custom-models/scripts/training_data_check.py \
  --matrix reference.csv --labels labels.txt --genes genes.txt
```

Use `with_mean=False` for sparse data that should not be densified, and use `check_expression=False` only when the user intentionally trains on a subset such as highly variable genes that cannot satisfy whole-transcriptome normalization checks.

### Export and Plot Results

Use the visualization sub-skill when the user already has an `AnnotationResult`:

```python
adata = predictions.to_adata(insert_labels=True, insert_conf=True, insert_prob=True)
predictions.to_table(folder="results", prefix="query_", xlsx=True)
```

For `celltypist.dotplot()`, remember that the default prediction column is `majority_voting`; use `use_as_prediction="predicted_labels"` when majority voting was not run.

## Shared References and Checks

- Read [troubleshooting](references/troubleshooting.md) for install/import issues, model-cache/network surprises, optional GPU package behavior, data-format problems, and workflow routing.
- Read [CLI and containers](references/cli-and-containers.md) for command patterns, Docker/Singularity notes, and safe smoke checks.
- Read [repo provenance](references/repo-provenance.md) before deciding whether this skill matches a current CellTypist checkout or needs refresh.
- Run [celltypist_cli_smoke.py](scripts/celltypist_cli_smoke.py) to check that the installed `celltypist` command exposes expected options without running downloads or annotation.

## Safety and Self-Containment

- Do not rely on original repository notebooks, docs, or source files at runtime; this skill bundles distilled references and safe helper scripts.
- Do not call model download APIs in offline or restricted environments unless the user explicitly wants network access.
- Treat built-in model files and remote model indexes as runtime data dependencies, not as part of this skill.
- Use local model paths with `./` or absolute paths for strict offline loading; bare filenames can trigger built-in inventory checks.
