---
name: pydeseq2
description: "Route PyDESeq2 bulk RNA-seq differential expression analysis tasks
  across data validation, DEA fitting, statistical results, and model
  internals."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# PyDESeq2 Repo Skill

Use this repo skill when a task involves PyDESeq2, the Python implementation of DESeq2-like bulk RNA-seq differential expression analysis. It helps agents prepare raw count data, fit `DeseqDataSet` models, compute `DeseqStats` results, troubleshoot design/contrast problems, and inspect advanced normalization or VST internals.

## Quick Start

1. Install PyDESeq2 in the active Python environment: `python -m pip install pydeseq2`.
2. Run a lightweight import check from this skill root: `python scripts/check_pydeseq2_environment.py`.
3. Route the task to the nearest sub-skill before writing code or running analysis.
4. Keep count matrices samples x genes and metadata indexed by the same sample IDs.
5. Bound CPU use explicitly in examples, usually with `DefaultInference(n_cpus=1)` or a user-approved count.

## Route By Task

- `sub-skills/data-io-validation/SKILL.md`: read this for count/metadata CSVs, orientation fixes, index alignment, `AnnData` construction, formula/design matrix prerequisites, and validation errors before modeling.
- `sub-skills/dea-workflows/SKILL.md`: read this for end-to-end `DeseqDataSet.deseq2()` workflows, single-factor and multi-factor designs, continuous covariates, outlier refit, low-memory mode, fitted object exports, and safe synthetic smoke runs.
- `sub-skills/statistics-and-results/SKILL.md`: read this after fitting a dataset to choose contrasts, run `DeseqStats.summary()`, interpret `results_df`, use thresholded tests, shrink LFCs, export tables, or create MA plots.
- `sub-skills/model-fitting-internals/SKILL.md`: read this for staged fitting order, size-factor methods, `deseq2_norm*` helpers, dispersion/LFC internals, Cooks outliers, VST, train/test normalization, and AnnData storage keys.

## Core Workflow Shape

```python
from pydeseq2.dds import DeseqDataSet
from pydeseq2.default_inference import DefaultInference
from pydeseq2.ds import DeseqStats

inference = DefaultInference(n_cpus=1)
dds = DeseqDataSet(
    counts=counts_df,
    metadata=metadata,
    design="~condition",
    inference=inference,
    quiet=True,
)
dds.deseq2()
stat_res = DeseqStats(dds, contrast=["condition", "B", "A"], quiet=True)
stat_res.summary()
results_df = stat_res.results_df
```

## Shared References

- `references/package-overview.md`: package scope, supported Python/dependencies, object model, and when PyDESeq2 is or is not a fit.
- `references/troubleshooting.md`: cross-cutting install/import, dependency, plotting, CPU, data, and package-scope failures.
- `references/repo-provenance.md`: source snapshot and evidence baseline for deciding whether this skill is stale.
- `references/repo-routing-metadata.json`: structured import metadata consumed by DisCo's `repo-skills-router` update process.

## Shared Script

- `scripts/check_pydeseq2_environment.py`: verifies package metadata, imports, synthetic fixture loading, and optional tiny fitting with `--smoke-fit`.

Run the script with `python scripts/check_pydeseq2_environment.py --json` when another agent needs machine-readable environment facts.

## Important Defaults

- PyDESeq2 expects raw non-negative integer counts, not normalized expression values.
- `DeseqDataSet` stores intermediate model state in AnnData fields such as `obs`, `var`, `varm`, `layers`, `obsm`, and `uns`.
- `DeseqDataSet.deseq2()` fits the model; `DeseqStats.summary()` computes the result table.
- Result log-fold changes in `results_df` are log2 scale; internal `dds.varm["LFC"]` values are natural-log scale.
- List contrasts like `["condition", "B", "A"]` require formula-based designs; direct design matrices generally require numeric contrast vectors.
- Use `dds.to_picklable_anndata()` when a fitted object must be pickled.

## Boundaries

This skill is for using PyDESeq2 as a package. It does not cover maintainer-only docs builds, release automation, or extending the repository implementation itself. For repository maintenance tasks, use a Python repository maintenance skill instead of this package-usage skill.
