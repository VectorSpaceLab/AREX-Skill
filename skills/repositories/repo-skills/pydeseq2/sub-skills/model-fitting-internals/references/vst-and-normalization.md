# VST and Normalization Reference

This reference focuses on PyDESeq2 normalization helpers, size-factor modes, control genes, and variance-stabilizing transformation (VST) workflows.

## Size-Factor Choices

PyDESeq2 supports three `fit_size_factors` modes through `DeseqDataSet(..., size_factors_fit_type=...)` or `dds.fit_size_factors(fit_type=...)`.

| Mode | Use When | Behavior | Train/Test Suitability |
|---|---|---|---|
| `ratio` | Standard bulk RNA-seq counts where at least some genes have nonzero counts in all samples | Median-of-ratios using gene-wise log means; all-zero-log genes are filtered | Best supported for leakage-safe train/test transforms because `logmeans` and `filtered_genes` can be reused. |
| `poscounts` | Sparse data where ratio mode would depend on too few no-zero genes | Uses positive counts only, based on the n-th root of nonzero products; excludes all-zero genes | Useful for fitting a dataset, but not exposed as a standalone fit/transform pair. |
| `iterative` | Every gene has at least one zero, or the user explicitly wants iterative MLE size factors | Iteratively alternates dispersion-related estimates and size-factor optimization | Not leakage-safe for held-out transforms because external `vst_transform(counts=...)` recomputes logmeans from the provided counts when no training logmeans exist. |

If the user asks for standard DESeq2-like defaults, start with `ratio`. If PyDESeq2 warns that every gene has at least one zero and switches to iterative mode, explain that ratio log geometric means are unavailable.

## Standalone Preprocessing Helpers

The helper functions in `pydeseq2.preprocessing` work on a pandas DataFrame or NumPy array whose rows are samples and columns are genes.

```python
from pydeseq2.preprocessing import deseq2_norm
from pydeseq2.preprocessing import deseq2_norm_fit
from pydeseq2.preprocessing import deseq2_norm_transform

normed_counts, size_factors = deseq2_norm(counts)
logmeans, filtered_genes = deseq2_norm_fit(train_counts)
test_normed, test_size_factors = deseq2_norm_transform(
    test_counts, logmeans, filtered_genes
)
```

Key facts:

- `deseq2_norm(counts)` is convenience shorthand for fit followed by transform on the same matrix.
- `deseq2_norm_fit(counts)` returns `logmeans` and `filtered_genes` for median-of-ratios normalization.
- `deseq2_norm_transform(counts, logmeans, filtered_genes)` reuses fitted training facts to normalize another count matrix.
- Pandas inputs preserve a pandas normalized-count output; size factors are returned as a one-dimensional array-like value.
- Gene order and number of columns must match between fit and transform. Align held-out counts to the same gene columns before transforming.

## Leakage-Safe Train/Test Normalization

Use this pattern when a user asks to normalize held-out samples without leakage:

1. Split counts by samples, keeping identical gene columns.
2. Fit `logmeans, filtered_genes = deseq2_norm_fit(train_counts)` on training counts only.
3. Transform training counts with `deseq2_norm_transform(train_counts, logmeans, filtered_genes)` if needed.
4. Transform held-out counts with `deseq2_norm_transform(test_counts, logmeans, filtered_genes)`.
5. Report both normalized counts and held-out size factors.

Do not call `deseq2_norm(test_counts)` for held-out data in a modeling pipeline, because it fits normalization facts on held-out samples.

Use the bundled `scripts/check_normalization.py` for a safe demonstration that uses a tiny local matrix.

## Control Genes

Control genes restrict size-factor fitting to known invariant genes.

```python
dds.fit_size_factors(control_genes=["gene4"])
```

Accepted indexers include:

- Gene-name strings such as `["ACTB", "GAPDH"]` when those names appear in `dds.var_names`.
- Integer gene positions such as `[0, 3, 7]`.
- Boolean masks with length equal to the number of genes.
- pandas indexes aligned to gene names.

Important behavior:

- Passing `control_genes` to `fit_size_factors()` overrides `dds.control_genes` for that call.
- Passing `control_genes` to `DeseqDataSet(...)` stores it for later default fitting.
- Ratio and poscounts modes still apply their usable-gene filtering, then intersect it with the control-gene mask.
- A bad gene name, wrong-length boolean mask, or inappropriate indexer fails through AnnData indexing; diagnose it as a gene-axis indexing problem.

## VST Workflows

PyDESeq2 exposes three VST methods:

| Method | Role | Main Outputs |
|---|---|---|
| `dds.vst(use_design=False, fit_type=None)` | Fit and transform the current dataset in one call | `dds.layers["vst_counts"]` plus VST fitting keys. |
| `dds.vst_fit(use_design=False)` | Fit VST size factors and dispersion trend without transforming external counts | `dds.obs["size_factors"]`, `dds.layers["normed_counts"]`, `dds.var["vst_genewise_dispersions"]`, and either `dds.uns["vst_trend_coeffs"]` or mean-trend state. |
| `dds.vst_transform(counts=None)` | Apply a previously fitted VST to current or external counts | Returns a NumPy array; `vst()` stores that array in `dds.layers["vst_counts"]`. |

### Blind Versus Design-Aware VST

- `use_design=False` temporarily replaces the design matrix with an intercept-only matrix during VST trend fitting, then restores the original design matrix.
- `use_design=True` uses the full design matrix for VST fitting and is mainly useful with `fit_type="parametric"`.
- If `use_design=True` is combined with mean VST, PyDESeq2 warns that design-aware VST is only useful for parametric fitting and proceeds through genewise VST dispersion fitting.

### VST Fit Types

- `fit_type=None` uses `dds.fit_type` as the VST fit type.
- `dds.vst(fit_type="parametric")` stores parametric VST coefficients in `dds.uns["vst_trend_coeffs"]`.
- `dds.vst(fit_type="mean")` uses `dds.var["vst_genewise_dispersions"]` and sets `dds.vst_fit_type = "mean"`.
- Choosing a VST `fit_type` should not change an already fitted DEA `dds.fit_type`.

### External VST Transform Pattern

Use this when the user needs VST for train/test data:

```python
train_dds = DeseqDataSet(
    counts=train_counts,
    metadata=train_metadata,
    design="~condition",
    size_factors_fit_type="ratio",
    quiet=True,
)
train_dds.vst_fit(use_design=False)
train_vst = train_dds.vst_transform()
test_vst = train_dds.vst_transform(test_counts.to_numpy())
```

Cautions:

- `vst_transform()` before `vst_fit()` raises `RuntimeError("The vst_fit method should be called prior to vst_transform.")` because size factors and trend keys are missing.
- Parametric VST transform also requires `dds.uns["vst_trend_coeffs"]`; if absent, fit the dispersion curve first through `vst_fit()` or `vst()`.
- External `counts` should have the same gene order as the training dataset.
- If size factors were fitted iteratively and `dds.logmeans` is unavailable, external `vst_transform(counts=...)` warns and recomputes logmeans from the counts being transformed. Treat this as leakage in train/test settings.

## Inspecting Expected VST Keys

After `dds.vst(use_design=False, fit_type="parametric")`, expect at least:

- `dds.obs["size_factors"]`
- `dds.layers["normed_counts"]`
- `dds.var["vst_genewise_dispersions"]`
- `dds.var["_genewise_converged"]`
- `dds.uns["vst_trend_coeffs"]`
- `dds.layers["vst_counts"]`

After `dds.vst(use_design=False, fit_type="mean")`, expect at least:

- `dds.obs["size_factors"]`
- `dds.layers["normed_counts"]`
- `dds.var["vst_genewise_dispersions"]`
- `dds.uns["mean_disp"]`
- `dds.layers["vst_counts"]`

## Normalization Sanity Checks

When debugging unexpected normalized counts:

- Confirm the count matrix is samples by genes, not genes by samples.
- Confirm all values are non-negative integer counts before constructing `DeseqDataSet`.
- Confirm sample rows and metadata rows align if using `DeseqDataSet`.
- Confirm gene columns match exactly between training and held-out matrices for `deseq2_norm_transform`.
- Inspect `dds.obs["size_factors"]`; extreme size factors usually indicate sample library-size imbalance, sparse data, or inappropriate control genes.
- Inspect `dds.var["_normed_means"]` after fitting size factors.
