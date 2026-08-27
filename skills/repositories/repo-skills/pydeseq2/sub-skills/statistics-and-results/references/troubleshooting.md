# Statistics and Results Troubleshooting

Use this reference when `DeseqStats`, result export, shrinkage, or MA plotting fails or produces confusing values.

## Fitted-State Errors

### `Please provide a fitted DeseqDataSet by first running the deseq2 method.`

Cause: `DeseqStats` was initialized before `dds.varm["LFC"]` existed.

Fix: fit the dataset first, usually with `dds.deseq2()`, or complete the staged fitting sequence that produces size factors, dispersions, and LFCs. Route full fitting questions to `../dea-workflows/SKILL.md` and staged fitting questions to `../model-fitting-internals/SKILL.md`.

### `dds has 'refit_cooks' set to True but Cooks outliers have not been refitted.`

Cause: the fitted `DeseqDataSet` expects Cook's outlier refitting, but `dds.refit()` was skipped.

Fix: prefer the high-level `dds.deseq2()` workflow, which handles the expected sequence, or explicitly run the staged Cook's/refit steps before constructing `DeseqStats`. If outlier refitting is intentionally disabled, create the dataset with `refit_cooks=False` before fitting.

## Contrast Errors

### Contrast list too short

Symptom: `IndexError` when using a list such as `contrast=["condition", "B"]`.

Fix: list contrasts require exactly three entries:

```python
contrast=["factor_name", "tested_level", "reference_level"]
```

### Unknown factor, tested level, or reference level

Symptoms: `ValueError` from `DeseqStats` or the formulaic contrast machinery.

Fixes:

- Check the design formula and metadata columns used to fit `dds`.
- Check actual category labels in the metadata, including capitalization and whitespace.
- Use levels that existed during fitting; do not invent a reference level after fitting.
- For pairwise categorical comparisons, use `contrast=[factor, tested, reference]`, where `tested` and `reference` are values from that factor.

### Numeric contrast wrong length

Symptom: `ValueError: The contrast vector must have the same length as the design matrix.`

Fix: create the vector from the fitted design matrix width:

```python
import numpy as np

columns = list(dds.obsm["design_matrix"].columns)
contrast = np.zeros(len(columns))
contrast[columns.index("condition[T.B]")] = 1
stat_res = DeseqStats(dds, contrast=contrast)
```

### List contrast with a precomputed design matrix

Symptom: `AttributeError` saying `cond()` or `contrast()` requires a formula-based design, or list contrasts cannot map to factor metadata.

Cause: a direct pandas design matrix does not carry formulaic contrast metadata.

Fix: pass a numeric contrast vector aligned to `dds.obsm["design_matrix"].columns`. Explain that coefficient naming and pairwise level helpers are limited to formula-based designs; direct design matrices use the column names supplied by the matrix.

## Thresholded Test Errors

### Negative `lfc_null` with `greaterAbs` or `lessAbs`

Symptom: `ValueError` requesting a positive `lfc_null`.

Cause: absolute-threshold tests use symmetric `+lfc_null` and `-lfc_null` bounds, so PyDESeq2 requires a non-negative threshold.

Fix: use `lfc_null=abs(value)` for `greaterAbs` or `lessAbs`, or switch to directional `greater`/`less` if a negative directional threshold is intended.

### Changed threshold but stale interpretation

Symptom: the table appears inconsistent with a newly requested threshold.

Fix: call `summary(lfc_null=..., alt_hypothesis=...)` to rerun the Wald test and rebuild `results_df`. Direct `run_wald_test()` is lower level; it does not by itself apply filtering and rebuild the exported table.

## Shrinkage Errors and Side Effects

### `KeyError` from `lfc_shrink(coeff=...)`

Cause: `coeff` is not one of the fitted LFC coefficient columns.

Fix: inspect available coefficients and pass an exact name:

```python
print(list(stat_res.LFC.columns))
print(list(dds.varm["LFC"].columns))
stat_res.lfc_shrink(coeff="condition[T.B]")
```

Common coefficient names include `condition[T.B]` for categorical formula terms, continuous covariate names such as `measurement`, and user-supplied design-matrix column names.

### Shrinkage changed the result table

Cause: `lfc_shrink()` mutates `stat_res.LFC`, `stat_res.SE`, and existing `results_df["log2FoldChange"]`/`results_df["lfcSE"]`. It sets `stat_res.shrunk_LFCs = True`.

Fix: if both unshrunk and shrunk tables are needed, copy the unshrunk table before shrinkage:

```python
stat_res.summary()
unshrunk = stat_res.results_df.copy()
stat_res.lfc_shrink(coeff="condition[T.B]")
shrunk = stat_res.results_df.copy()
```

### Shrinkage did not recompute p-values

This is expected. PyDESeq2 shrinkage is for effect-size stabilization and leaves p-values/adjusted p-values unchanged. For thresholded p-values, rerun `summary(lfc_null=..., alt_hypothesis=...)` before shrinkage and report that p-values are from the thresholded Wald test while LFC/SE columns are shrunk afterward.

### Warning about NaN or infinite shrinkage values

Cause: some genes produced invalid shrinkage estimates; PyDESeq2 keeps their previous LFC/SE values.

Fix: report the warning, check whether affected genes are all-zero or very low information, and avoid treating unchanged shrunk values as high-confidence estimates.

## Plotting Errors

### `Trying to make an MA plot but p-values were not computed yet.`

Cause: `plot_MA()` was called before `summary()` created `results_df`.

Fix:

```python
stat_res.summary()
stat_res.plot_MA(save_path="ma.png")
```

### MA plot has unexpected threshold lines

Cause: `plot_MA()` draws the active `lfc_null`. For `greaterAbs` and `lessAbs`, it also draws `-lfc_null`.

Fix: verify the most recent `summary(lfc_null=..., alt_hypothesis=...)` call and rerun it if the active threshold changed.

## NaN P-Values and Adjusted P-Values

Expected causes:

- All-zero genes or genes with insufficient information.
- Cook's-distance filtering when `cooks_filter=True`.
- Independent filtering of low-information genes when `independent_filter=True`.
- Invalid p-values that are omitted from Benjamini-Hochberg adjustment.

Fixes:

- Keep `NaN` values visible in exports.
- Compare with `independent_filter=False` when a user asks why `padj` is `NaN` despite a finite `pvalue`.
- Compare with `cooks_filter=False` only when diagnosing outlier-filtering behavior; do not disable filtering silently in final analysis.

## Log2 Versus Natural-Log Confusion

Symptoms: effect sizes differ by a factor of about `ln(2)` or thresholds seem off.

Facts:

- `results_df["log2FoldChange"]` and `results_df["lfcSE"]` are in log2 units.
- `lfc_null` is supplied by users in log2 units.
- Internal fitted LFC matrices and the Wald routine use natural-log units.
- PyDESeq2 converts user-facing values internally; do not multiply `lfc_null` by `np.log(2)` before passing it to `summary()`.

## Export Surprises

### Missing gene identifiers in CSV

Cause: writing CSV with `index=False` discards gene IDs stored in the DataFrame index.

Fix:

```python
stat_res.results_df.to_csv("results.csv", index=True)
```

### Top hits exclude genes with `NaN` adjusted p-values

Cause: normal pandas sorting and filtering can drop or hide `NaN` values.

Fix: sort with `na_position="last"` and report how many `padj` values are missing.
