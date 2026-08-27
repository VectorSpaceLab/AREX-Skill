---
name: dea-workflows
description: "Run practical PyDESeq2 differential expression workflows with
  DeseqDataSet and DeseqStats."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# PyDESeq2 DEA Workflows

Use this sub-skill when an agent needs to run an end-to-end PyDESeq2 differential expression analysis after count and metadata inputs are already validated.

## Route First

- For CSV loading, count orientation, metadata/index alignment, `AnnData` setup, and input validity failures, use `../data-io-validation/SKILL.md`.
- For p-value interpretation, result columns, alternative hypotheses, LFC shrinkage details, and MA plots, use `../statistics-and-results/SKILL.md`.
- For stepwise fitting internals, normalization helpers, VST, and advanced model-state inspection, use `../model-fitting-internals/SKILL.md`.

## Standard Flow

1. Start from a samples-by-genes raw count table and metadata indexed by the same sample IDs.
2. Bound parallelism explicitly with `DefaultInference(n_cpus=1)` or another user-approved CPU count.
3. Build `DeseqDataSet(counts=..., metadata=..., design="~condition", inference=..., refit_cooks=True)`.
4. Run `dds.deseq2()` once to fit size factors, dispersions, LFCs, Cook's distances, and optional outlier refit.
5. Create one or more `DeseqStats(dds, contrast=...)` objects from the fitted dataset and call `summary()`.
6. Export `stats.results_df` to CSV when the user wants a table; export `dds.to_picklable_anndata()` only when the fitted object itself is needed.

## Quick Commands

- From this sub-skill directory, run the bundled script on PyDESeq2 synthetic example data: `python scripts/run_synthetic_dea.py --n-cpus 1 --quiet`.
- Save a results table: `python scripts/run_synthetic_dea.py --output-csv results.csv --overwrite --quiet`.
- Try a multi-factor design on PyDESeq2 synthetic example data: `python scripts/run_synthetic_dea.py --design "~group + condition" --contrast condition B A --filter-column group --quiet`.

## Reference Map

- `references/workflows.md` gives copyable single-factor, multi-factor, continuous-factor, low-memory, outlier-refit, and export skeletons.
- `references/api-reference.md` summarizes the PyDESeq2 0.5.4 workflow APIs and object handoff contract.
- `references/troubleshooting.md` covers common end-to-end DEA workflow failures and safe fixes.
