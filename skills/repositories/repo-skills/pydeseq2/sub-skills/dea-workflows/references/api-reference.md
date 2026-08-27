# DEA Workflow API Reference

This reference summarizes PyDESeq2 0.5.4 APIs needed for end-to-end differential expression workflows.

## Package Scope

PyDESeq2 is a Python implementation of DESeq2-like bulk RNA-seq differential expression analysis. Version 0.5.4 supports default-style DESeq2 workflows for single-factor and multi-factor analysis with categorical or continuous factors using Wald tests. It is a reimplementation, so exact values and feature coverage can differ from R DESeq2.

Python requirement: `>=3.11`.

Core runtime dependencies include `anndata`, `formulaic`, `formulaic-contrasts`, `numpy`, `pandas`, `scikit-learn`, `scipy`, and `matplotlib`.

## `DefaultInference`

```python
DefaultInference(
    joblib_verbosity=0,
    batch_size=128,
    n_cpus=None,
    backend="loky",
)
```

- Controls the default scipy/sklearn/numpy inference routines.
- Uses joblib internally for parallel operations.
- `n_cpus=None` means all available CPUs; use a small explicit value in reusable workflows.
- Pass the same inference object to `DeseqDataSet` and `DeseqStats` when you want consistent CPU behavior.

## `DeseqDataSet`

```python
DeseqDataSet(
    *,
    adata=None,
    counts=None,
    metadata=None,
    design="~condition",
    fit_type="parametric",
    size_factors_fit_type="ratio",
    control_genes=None,
    min_mu=0.5,
    min_disp=1e-8,
    max_disp=10.0,
    refit_cooks=True,
    min_replicates=7,
    beta_tol=1e-8,
    n_cpus=None,
    inference=None,
    quiet=False,
    low_memory=False,
)
```

Important workflow arguments:

- `counts`: samples-by-genes raw counts with non-negative integer values.
- `metadata`: sample metadata indexed by sample IDs.
- `adata`: alternative input carrying counts in `X` and metadata in `obs`.
- `design`: a formulaic string such as `"~condition"`, `"~group + condition"`, or `"~group + condition + measurement"`; may also be a design matrix `DataFrame`.
- `fit_type`: `"parametric"` or `"mean"` for dispersion-mean trend fitting.
- `size_factors_fit_type`: `"ratio"`, `"poscounts"`, or `"iterative"`.
- `refit_cooks`: whether to replace/refit Cook's outliers when possible.
- `min_replicates`: minimum replicate count required for Cook's outlier replacement.
- `low_memory`: deletes no-longer-needed intermediate matrices during fitting.
- `quiet`: suppresses progress prints.

Deprecated arguments to avoid in new workflow examples: `design_factors`, `continuous_factors`, and `ref_level`.

## `DeseqDataSet.deseq2()`

```python
dds.deseq2(fit_type=None)
```

This is the standard first-stage DEA wrapper. It runs:

1. `fit_size_factors()` using the configured size-factor method.
2. `fit_genewise_dispersions()`.
3. `fit_dispersion_trend()`.
4. `fit_dispersion_prior()`.
5. `fit_MAP_dispersions()`.
6. `fit_LFC()`.
7. `calculate_cooks()`.
8. `refit()` when `refit_cooks=True`.
9. Cook's outlier mask calculation.

`fit_type` passed to `deseq2()` overrides the dataset's `fit_type` for the DEA run.

## Fitted Object State

`DeseqDataSet` extends `AnnData`. Useful fitted fields include:

- `dds.X`: raw count matrix.
- `dds.obs`: sample-level metadata plus fitted sample fields such as `size_factors`.
- `dds.obsm["design_matrix"]`: formulaic or user-provided design matrix.
- `dds.var`: gene-level fields such as dispersions, normalized means, and outlier/refit flags.
- `dds.varm["LFC"]`: fitted log-fold-change coefficients in natural-log scale.
- `dds.layers`: intermediate arrays such as normalized counts and Cook's distances, unless removed by `low_memory=True`.

`DeseqStats.summary()` reports `log2FoldChange` in log2 scale, while `dds.varm["LFC"]` stores natural-log LFC coefficients.

## `DeseqStats`

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

`dds` must already be fitted with `dds.deseq2()` or with the equivalent staged fitting sequence that creates `dds.varm["LFC"]`.

`contrast` is required and may be either:

- A list of three strings: `["variable", "tested_level", "reference_level"]`, for formula-based designs.
- A numeric vector with the same length as `dds.obsm["design_matrix"].shape[1]`, for continuous effects or direct design matrices.

`summary()` runs the Wald test, Cook's filtering, adjusted p-value calculation, and stores a table in `stats.results_df`.

Common `results_df` columns:

- `baseMean`
- `log2FoldChange`
- `lfcSE`
- `stat`
- `pvalue`
- `padj`

## Multiple Contrasts From One Fit

```python
dds.deseq2()

contrasts = {
    "condition_B_vs_A": ["condition", "B", "A"],
    "group_Y_vs_X": ["group", "Y", "X"],
}

results = {}
for name, contrast in contrasts.items():
    stats = DeseqStats(dds, contrast=contrast, quiet=True)
    stats.summary()
    results[name] = stats.results_df.copy()
```

Do not refit `dds` for every categorical contrast when the model design is unchanged. Refit only if the user changes the model formula, filtering, count data, metadata, or fitting options.

## Export Methods

- Result tables: `stats.results_df.to_csv(path)`.
- Picklable fitted object: `dds.to_picklable_anndata()` followed by AnnData write methods such as `.write_h5ad(path)` when the optional storage dependencies are available.
- Avoid raw object pickle in reusable scripts unless the user explicitly asks for it.
