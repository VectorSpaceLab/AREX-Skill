# DEA Workflow Troubleshooting

Use this reference for failures that happen while constructing, fitting, or handing off `DeseqDataSet`/`DeseqStats` workflows. For raw count/metadata repair, route to `../data-io-validation/SKILL.md`.

## Missing Metadata Columns

Symptom: formulaic/design errors, `ValueError`, or missing variables when using `design="~condition"` or another formula.

Fix:

- Confirm every variable named in the design exists in `metadata.columns`.
- Remove or impute samples with missing values before constructing `DeseqDataSet`.
- Keep metadata indexed by the same sample IDs as `counts_df.index`.

## Single-Level Factors

Symptom: the design has no meaningful comparison, or PyDESeq2 warns that the design matrix is not full rank.

Fix:

- Check `metadata["condition"].value_counts(dropna=False)` or the relevant factor.
- Differential expression for a factor requires at least two represented levels after filtering.
- If a factor only has one level, remove it from the design or add valid samples from another level.

## Rank-Deficient Designs

Symptom: warning that the design matrix is not full rank; later DEA fitting may fail or produce invalid comparisons.

Common causes:

- Redundant columns such as `condition` and a perfectly correlated `batch`.
- Too many design terms for too few samples.
- Empty factor levels after filtering.

Fix:

- Simplify the formula, for example from `"~batch + condition"` to `"~condition"` when batch is perfectly confounded.
- Inspect `dds.obsm["design_matrix"].columns` and sample counts per factor combination.
- Avoid DEA if the biological comparison is fully confounded with batch.

## Fitting Before `DeseqStats`

Symptom: `AssertionError: Please provide a fitted DeseqDataSet by first running the deseq2 method.`

Fix:

```python
dds = DeseqDataSet(counts=counts_df, metadata=metadata, design="~condition")
dds.deseq2()
stats = DeseqStats(dds, contrast=["condition", "B", "A"])
stats.summary()
```

`DeseqStats` requires `dds.varm["LFC"]`, which is created by `dds.deseq2()` or the equivalent staged fitting flow.

## Cook's Refit Was Not Performed

Symptom: `DeseqStats` raises that `dds` has `refit_cooks=True` but Cooks outliers have not been refitted.

Fix:

- Prefer running the full `dds.deseq2()` wrapper, which calculates Cooks distances and calls `refit()` when `refit_cooks=True`.
- If running staged internals manually, call `dds.calculate_cooks()` and `dds.refit()` before `DeseqStats`, or set `refit_cooks=False` before fitting if outlier replacement is not desired.
- Route detailed staged-method ordering to `../model-fitting-internals/SKILL.md`.

## Outlier Genes Were Not Refit

Symptom: the user expected Cook's outlier replacement but sees no refitted genes, often in a small cohort.

Explanation:

- `refit_cooks=True` enables the replacement/refit path, but replacement only applies when enough replicate samples are available.
- `min_replicates` defaults to `7`; samples in groups with fewer replicates are not replaceable.
- PyDESeq2 may still compute Cooks distances and run without refitting any genes.

Fix:

- Inspect `dds.var.get("replaced")`, `dds.var.get("refitted")`, and `dds.obs.get("replaceable")` after fitting.
- Lower `min_replicates` only when the user understands the statistical implications.
- For tiny cohorts, explain that no-replacement behavior can be expected even with `refit_cooks=True`.

## Joblib CPU Overuse

Symptom: workflow uses too many processes or slows shared machines.

Fix:

- Pass `DefaultInference(n_cpus=1)` or another explicit approved value.
- Reuse the same inference object in `DeseqDataSet` and `DeseqStats`.
- Avoid `n_cpus=None` in scripts because it means all available CPUs.

## `fit_type` Choice

Use `fit_type="parametric"` by default. Switch to `fit_type="mean"` when the user requests the mean dispersion fit or the parametric trend is unsuitable for the dataset.

`dds.deseq2(fit_type="mean")` can override the initialization value for that DEA run.

## Zero-Heavy Counts and Size Factors

Symptom: warning that every gene contains at least one zero and PyDESeq2 cannot compute log geometric means.

Explanation and fix:

- Default `size_factors_fit_type="ratio"` switches to iterative mode when every gene has at least one zero.
- For zero-heavy data, consider initializing with `size_factors_fit_type="poscounts"` or `"iterative"` if the user asks for that normalization behavior.
- All-zero genes or very low-count genes should usually be filtered before DEA.

## Wide Datasets and `low_memory`

Symptom: large genes-by-samples workloads consume too much memory.

Fix:

```python
dds = DeseqDataSet(
    counts=counts_df,
    metadata=metadata,
    design="~group + condition",
    low_memory=True,
    inference=DefaultInference(n_cpus=1),
)
dds.deseq2()
```

`low_memory=True` removes intermediate arrays after they are no longer needed. Do not rely on deleted intermediate layers for later inspection.

## Invalid Contrasts

Symptoms include `IndexError` for too-short list contrasts or `ValueError` for unknown factors/levels or numeric vectors with the wrong length.

Fix:

- List contrasts must be `["variable", "tested_level", "reference_level"]` and the variable/levels must exist in the formula-based design.
- Numeric contrast vectors must have exactly one element per design-matrix column.
- For continuous variables, inspect `dds.obsm["design_matrix"].columns` and set the coefficient position to `1`.
- For direct design matrices, use numeric contrasts rather than list contrasts.

## Unsupported DESeq2 Features

PyDESeq2 0.5.4 broadly covers default DESeq2-style single-factor and multi-factor Wald workflows with categorical or continuous factors, plus optional apeGLM LFC shrinkage. If a user asks for a feature not implemented by PyDESeq2, such as a DESeq2 feature outside this scope, state that PyDESeq2 may not implement it and either choose the closest supported workflow or recommend using R DESeq2 for that specific feature.
