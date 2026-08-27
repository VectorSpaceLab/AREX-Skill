# Package Overview

## Purpose

Read this reference when deciding whether PyDESeq2 is the right package for a bulk RNA-seq differential expression task, or when you need a compact map of its objects and dependencies before routing to a sub-skill.

## What PyDESeq2 Provides

PyDESeq2 implements a Python workflow similar to DESeq2 for bulk RNA-seq differential expression analysis. The public package scope centers on:

- `DeseqDataSet`: an `AnnData` subclass that fits size factors, dispersions, log-fold changes, Cook's distances, and optional outlier refits.
- `DeseqStats`: Wald tests, p-value adjustment/filtering, result tables, LFC shrinkage, and MA plotting for a fitted `DeseqDataSet`.
- `DefaultInference`: NumPy/SciPy/scikit-learn/joblib-backed routines used by the default model-fitting methods.
- `pydeseq2.preprocessing`: standalone median-of-ratios normalization helpers.
- `pydeseq2.utils.load_example_data`: a small packaged synthetic dataset for examples and smoke tests.

PyDESeq2 0.5.4 declares Python `>=3.11` and depends on `anndata`, `formulaic`, `formulaic-contrasts`, `numpy`, `pandas`, `scikit-learn`, `scipy`, and `matplotlib`.

## Package Fit

Use PyDESeq2 when:

- The data are bulk RNA-seq raw counts with samples as observations and genes as variables.
- The user wants DESeq2-like single-factor, multi-factor, or continuous-factor differential expression analysis in Python.
- Wald tests and optional apeGLM-like LFC shrinkage are suitable.
- The workflow can use pandas DataFrames or AnnData objects.

Avoid or qualify PyDESeq2 when:

- The user supplies already-normalized expression values instead of raw counts.
- The task needs DESeq2 features not implemented by PyDESeq2's current API.
- The task is single-cell omics preprocessing or Scanpy-style analysis rather than bulk RNA-seq DEA.
- The user needs long-running benchmarking, documentation builds, or repository maintenance workflows rather than package usage.

## Object Handoff

The standard object flow is:

1. Validate `counts_df` and `metadata` in `sub-skills/data-io-validation/SKILL.md`.
2. Fit `dds = DeseqDataSet(...); dds.deseq2()` in `sub-skills/dea-workflows/SKILL.md`.
3. Compute `stat_res = DeseqStats(dds, contrast=...); stat_res.summary()` in `sub-skills/statistics-and-results/SKILL.md`.
4. Inspect staged internals or VST only when needed in `sub-skills/model-fitting-internals/SKILL.md`.

## Data Model

Counts should be a `pandas.DataFrame` where rows are samples and columns are genes. Metadata should be a `pandas.DataFrame` indexed by the same sample IDs. Formula designs such as `~condition` reference metadata columns; direct design matrices must align row-for-row with samples.

`DeseqDataSet` stores fitted quantities in AnnData-like fields:

- `obs`: sample-level fields such as `size_factors`.
- `var`: gene-level fields such as dispersions and normalized means.
- `varm`: gene x coefficient matrices such as `LFC`.
- `layers`: count-aligned matrices such as `normed_counts`, `cooks`, and `vst_counts`.
- `obsm`: sample x coefficient matrices such as `design_matrix`.
- `uns`: unstructured fit metadata such as trend and prior values.

## Bundled Checks

Run these from the skill root after installing PyDESeq2:

```bash
python scripts/check_pydeseq2_environment.py
python sub-skills/data-io-validation/scripts/validate_pydeseq2_inputs.py --use-synthetic --design '~condition'
python sub-skills/dea-workflows/scripts/run_synthetic_dea.py --n-cpus 1 --quiet
python sub-skills/statistics-and-results/scripts/summarize_results.py --contrast condition B A --n-cpus 1 --quiet
python sub-skills/model-fitting-internals/scripts/check_normalization.py --as-json
```

These checks use packaged synthetic data or tiny in-script fixtures and do not download data.
