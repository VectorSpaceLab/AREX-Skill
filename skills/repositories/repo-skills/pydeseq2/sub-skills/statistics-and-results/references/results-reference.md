# Results Reference

This reference is for statistical analysis after a `DeseqDataSet` is fitted. Keep raw input checks, full fitting workflows, and normalization internals in sibling sub-skills.

## Required State

`DeseqStats` requires a fitted `DeseqDataSet`. The object must already contain fitted LFCs in `dds.varm["LFC"]`, normalized means in `dds.var["_normed_means"]`, dispersions in `dds.var["dispersions"]`, sample size factors, and a design matrix in `dds.obsm["design_matrix"]`.

```python
from pydeseq2.ds import DeseqStats

stat_res = DeseqStats(dds, contrast=["condition", "B", "A"], quiet=True)
stat_res.summary()
results_df = stat_res.results_df
```

If the fitted object was created with `refit_cooks=True`, PyDESeq2 expects Cook's outliers to have been refitted before result analysis. Use the high-level `dds.deseq2()` workflow or the correct staged sequence rather than manually skipping `dds.refit()`.

## `DeseqStats` Constructor

Signature for PyDESeq2 0.5.4:

```python
DeseqStats(
    dds,
    contrast,
    alpha=0.05,
    cooks_filter=True,
    independent_filter=True,
    prior_LFC_var=None,
    lfc_null=0.0,
    alt_hypothesis=None,
    inference=None,
    quiet=False,
    n_cpus=None,
)
```

Important parameters:

- `contrast`: list of three strings or a NumPy vector aligned to design-matrix columns.
- `alpha`: significance threshold used for filtering/plot coloring and independent filtering decisions.
- `cooks_filter`: sets p-values to `NaN` for genes flagged as Cook's-distance outliers.
- `independent_filter`: uses base mean cutoffs before Benjamini-Hochberg adjustment; set `False` to adjust all non-NaN p-values directly.
- `lfc_null`: log2 fold-change threshold under the null hypothesis. PyDESeq2 converts it to natural-log units internally for the Wald test.
- `alt_hypothesis`: one of `greaterAbs`, `lessAbs`, `greater`, `less`, or `None`.
- `inference` and `n_cpus`: optionally share a `DefaultInference` or control parallel work.

## Contrast Rules

For formula-based designs, pass a list contrast:

```python
DeseqStats(dds, contrast=["condition", "B", "A"])
```

This tests condition `B` versus reference level `A`. PyDESeq2 builds the contrast vector with `dds.contrast(column="condition", baseline="A", group_to_compare="B")`, and can adapt the internal reference level without requiring a full refit for simple pairwise comparisons.

For precomputed design matrices, pass a numeric vector:

```python
import numpy as np

contrast_vector = np.zeros(dds.obsm["design_matrix"].shape[1])
contrast_vector[1] = 1
stat_res = DeseqStats(dds, contrast=contrast_vector)
```

Numeric contrast vectors must have exactly the same length as `dds.obsm["design_matrix"].shape[1]`. They are the correct route when `DeseqDataSet` was initialized with a pandas design matrix instead of a formula string, because `dds.cond()` and `dds.contrast()` require formulaic contrast metadata.

Inspect coefficient names before shrinkage or numeric contrast selection:

```python
print(list(dds.obsm["design_matrix"].columns))
print(list(dds.varm["LFC"].columns))
```

Categorical coefficient names commonly look like `condition[T.B]`; continuous covariates may use the column name such as `measurement`; direct design matrices keep the provided column names.

## Summary and Result Columns

`summary()` runs the Wald test when needed, applies Cook's filtering when enabled, adjusts p-values with either independent filtering or direct Benjamini-Hochberg correction, and writes `results_df`.

`results_df` columns:

- `baseMean`: gene-wise mean of normalized counts.
- `log2FoldChange`: contrast-specific LFC displayed in log2 scale.
- `lfcSE`: standard error displayed in log2 scale.
- `stat`: Wald statistic for the active contrast, `lfc_null`, and `alt_hypothesis`.
- `pvalue`: Wald-test p-value after Cook's filtering if enabled.
- `padj`: multiple-testing-adjusted p-value after independent filtering or direct BH adjustment.

Internally, fitted LFCs in `dds.varm["LFC"]` and `DeseqStats.LFC` are natural-log coefficients. `summary()` converts the contrast LFC and standard error to log2 for `results_df` by dividing by `np.log(2)`. User-facing `lfc_null` is log2, while the Wald routine receives `np.log(2) * lfc_null`.

## Wald Tests and Thresholded Alternatives

Default `summary()` with `alt_hypothesis=None` tests departure from the null LFC. To perform thresholded tests, pass `lfc_null` and `alt_hypothesis` at construction or during `summary()`:

```python
stat_res.summary(lfc_null=0.5, alt_hypothesis="greaterAbs")
```

Available alternatives:

- `greaterAbs`: find genes with absolute log2 fold change greater than `lfc_null`; `lfc_null` must be non-negative.
- `lessAbs`: find genes with absolute log2 fold change less than `lfc_null`; `lfc_null` must be non-negative.
- `greater`: find genes with log2 fold change greater than `lfc_null`; `lfc_null` may be negative.
- `less`: find genes with log2 fold change less than `lfc_null`; `lfc_null` may be negative.

Calling `summary()` again with a changed `lfc_null` or `alt_hypothesis` reruns the Wald test and rebuilds `results_df`. Calling `run_wald_test()` directly only updates p-values/statistics/SE; use `summary()` afterward to refresh filtering, adjusted p-values, and `results_df`.

## Filtering and NaNs

Cook's filtering and independent filtering can make valid result rows contain `NaN` p-values or adjusted p-values.

- All-zero genes or genes invalidated during outlier handling can produce non-informative statistics.
- With `cooks_filter=True`, p-values for Cook's outlier genes are set to `NaN`.
- With `independent_filter=True`, low-information genes may retain `NaN` in `padj` even when `pvalue` is present.
- With `independent_filter=False`, PyDESeq2 applies Benjamini-Hochberg to all non-NaN p-values directly.

When exporting, sort with `na_position="last"` and do not silently fill `NaN` adjusted p-values as significant values.

```python
ranked = stat_res.results_df.sort_values("padj", na_position="last")
ranked.to_csv("results.csv")
```

## LFC Shrinkage

Use shrinkage for visualization and post-processing of effect sizes, not to recompute p-values:

```python
stat_res.summary()
stat_res.lfc_shrink(coeff="condition[T.B]", adapt=True)
shrunk = stat_res.results_df
```

`lfc_shrink(coeff, adapt=True)`:

- Uses apeGLM-style shrinkage for one coefficient.
- Requires `coeff` to be a column in `stat_res.LFC`/`dds.varm["LFC"]`.
- Mutates `stat_res.LFC`, `stat_res.SE`, and existing `results_df["log2FoldChange"]`/`results_df["lfcSE"]`.
- Sets `stat_res.shrunk_LFCs = True`.
- Leaves `pvalue`, `padj`, and the previously computed Wald test semantics unchanged.

If a user asks for thresholded tests and shrinkage, run `summary(lfc_null=..., alt_hypothesis=...)` first to compute the thresholded p-values, then run `lfc_shrink()` and explicitly explain that the effect-size columns are shrunk while the p-values remain from the pre-shrink Wald test. If they want p-values after changing the threshold, rerun `summary()` with the threshold before shrinkage.

## MA Plots

`plot_MA(log=True, save_path=None, **kwargs)` requires `summary()` first because it reads `results_df`.

```python
stat_res.summary(lfc_null=0.5, alt_hypothesis="greaterAbs")
stat_res.plot_MA(log=True, save_path="ma.png", s=20, alpha=0.5)
```

The plot uses `baseMean` on the x-axis and `log2FoldChange` on the y-axis. Points with `padj < alpha` are colored differently. A horizontal line marks `lfc_null`; for `greaterAbs` and `lessAbs`, a second horizontal line marks `-lfc_null`.

## Export Checklist

Before handing result tables to users:

1. Confirm the contrast and coefficient names used.
2. State whether `cooks_filter` and `independent_filter` were enabled.
3. State whether `lfc_null`/`alt_hypothesis` changed the p-value semantics.
4. State whether `log2FoldChange` and `lfcSE` are shrunk or unshrunk.
5. Preserve gene IDs in the DataFrame index when writing CSV.
6. Keep `NaN` p-values/adjusted p-values visible rather than converting them to zero.
