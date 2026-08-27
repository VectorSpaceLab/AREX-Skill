---
name: statistics-and-results
description: "Compute, interpret, export, and troubleshoot PyDESeq2 statistical
  results after fitting a DeseqDataSet."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# PyDESeq2 Statistics and Results

Use this sub-skill after a `DeseqDataSet` has already been fitted with `dds.deseq2()` or the equivalent staged fitting steps. It covers `DeseqStats`, contrasts, Wald-test summaries, adjusted p-values, log-fold-change shrinkage, MA plots, and result-table interpretation.

## When To Use

- Build a `DeseqStats(dds, contrast=...)` object for a fitted `DeseqDataSet`.
- Compare categorical levels with `contrast=[factor, tested_level, reference_level]` or use a numeric contrast vector for direct design matrices.
- Run `summary()`, thresholded tests with `lfc_null` and `alt_hypothesis`, or `run_wald_test()` when a lower-level rerun is needed.
- Interpret `results_df` columns, p-value filtering, NaN behavior, coefficient names, and log2 versus natural-log scales.
- Apply `lfc_shrink(coeff, adapt=True)` and make `plot_MA(log=True, save_path=None, **kwargs)` outputs.

## Route Elsewhere

- For raw count/metadata loading, CSV/index validation, AnnData setup, and design-matrix input checks, use `../data-io-validation/SKILL.md`.
- For complete fitting workflows that create the fitted `DeseqDataSet`, use `../dea-workflows/SKILL.md`.
- For staged normalization, dispersion, LFC fitting, VST, and internal AnnData keys, use `../model-fitting-internals/SKILL.md`.

## Minimal Result Pattern

```python
from pydeseq2.ds import DeseqStats

stat_res = DeseqStats(
    dds,
    contrast=["condition", "B", "A"],
    alpha=0.05,
    cooks_filter=True,
    independent_filter=True,
    quiet=True,
)
stat_res.summary()
results = stat_res.results_df.sort_values("padj", na_position="last")
```

Use `results_df` for exports and ranking. It contains `baseMean`, `log2FoldChange`, `lfcSE`, `stat`, `pvalue`, and `padj` after `summary()`.

## Key References

- `references/results-reference.md` gives result-column semantics, contrast forms, thresholded tests, shrinkage behavior, coefficient naming, and MA-plot usage.
- `references/troubleshooting.md` maps common runtime errors and confusing outputs to fixes.
- `scripts/summarize_results.py` runs a safe synthetic workflow with flags for contrast, thresholded tests, shrinkage, MA plotting, CSV export, and independent filtering.

## Safe Script

Run the bundled script after installing PyDESeq2. From the `pydeseq2` skill root, use:

```bash
python scripts/summarize_results.py --help
python scripts/summarize_results.py --contrast condition B A --output-csv results.csv --ma-plot ma.png
```

The script uses PyDESeq2's packaged synthetic dataset by default, performs a small fit, and does not download data or mutate files unless explicit output paths are provided.
