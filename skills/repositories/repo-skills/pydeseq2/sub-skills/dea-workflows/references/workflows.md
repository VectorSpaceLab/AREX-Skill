# End-to-End DEA Workflows

This reference assumes validated inputs: a raw-count `pandas.DataFrame` with samples as rows and genes as columns, plus metadata indexed by the same sample IDs. Route input loading and validation to `../data-io-validation/SKILL.md`.

## Minimal Single-Factor Workflow

```python
from pydeseq2.dds import DeseqDataSet
from pydeseq2.default_inference import DefaultInference
from pydeseq2.ds import DeseqStats

inference = DefaultInference(n_cpus=1)

dds = DeseqDataSet(
    counts=counts_df,
    metadata=metadata,
    design="~condition",
    refit_cooks=True,
    inference=inference,
    quiet=True,
)
dds.deseq2()

stats = DeseqStats(
    dds,
    contrast=["condition", "B", "A"],
    inference=inference,
    quiet=True,
)
stats.summary()
results_df = stats.results_df
```

`dds.deseq2()` fits size factors, genewise dispersions, dispersion trend/prior, MAP dispersions, LFCs, Cook's distances, optional Cook's outlier refit, and a Cook's outlier mask. Do not create `DeseqStats` before this call; `DeseqStats` requires `dds.varm["LFC"]`.

## Recommended Pre-Fit Filtering

Do lightweight filtering before constructing `DeseqDataSet`:

```python
factor = "condition"
samples_to_keep = ~metadata[factor].isna()
counts_df = counts_df.loc[samples_to_keep]
metadata = metadata.loc[samples_to_keep]

genes_to_keep = counts_df.columns[counts_df.sum(axis=0) >= 10]
counts_df = counts_df.loc[:, genes_to_keep]
```

This mirrors the bundled script's synthetic workflow: remove samples missing the design factor, then remove genes with low total counts. For comprehensive validation and orientation fixes, use `../data-io-validation/SKILL.md`.

## Multi-Factor Workflows

Use formulaic design strings to include multiple metadata columns:

```python
dds = DeseqDataSet(
    counts=counts_df,
    metadata=metadata,
    design="~group + condition",
    inference=DefaultInference(n_cpus=1),
    refit_cooks=True,
    quiet=True,
)
dds.deseq2()

condition_stats = DeseqStats(dds, contrast=["condition", "B", "A"], quiet=True)
condition_stats.summary()

group_stats = DeseqStats(dds, contrast=["group", "Y", "X"], quiet=True)
group_stats.summary()
```

Fit the `DeseqDataSet` once, then create multiple `DeseqStats` objects for multiple contrasts. This is the preferred pattern for requests such as comparing `condition B vs A` and `group Y vs X` from the same `~group + condition` model.

The list contrast has the form `["variable", "tested_level", "reference_level"]`. It can test any pair of levels represented in a formula-based design without refitting LFCs.

## Continuous Factors

PyDESeq2 0.5.4 automatically treats numeric variables in a formula as continuous. For a design such as `"~group + condition + measurement"`, test the continuous coefficient with a numeric contrast vector aligned to `dds.obsm["design_matrix"].columns`:

```python
import numpy as np

inference = DefaultInference(n_cpus=1)
dds = DeseqDataSet(
    counts=counts_df,
    metadata=metadata,
    design="~group + condition + measurement",
    inference=inference,
    quiet=True,
)
dds.deseq2()

print(list(dds.obsm["design_matrix"].columns))
contrast_vector = np.zeros(dds.obsm["design_matrix"].shape[1])
contrast_vector[list(dds.obsm["design_matrix"].columns).index("measurement")] = 1

measurement_stats = DeseqStats(dds, contrast=contrast_vector, inference=inference, quiet=True)
measurement_stats.summary()
```

If a numeric column should be categorical, use formulaic syntax such as `"~C(batch) + condition"` and inspect `dds.obsm["design_matrix"].columns` before choosing contrasts.

## Direct Design Matrices

`design` may be a `pandas.DataFrame` design matrix instead of a formula string. In that mode, `DeseqStats` supports numeric contrast vectors only; list contrasts such as `["condition", "B", "A"]` require a formula-based design.

```python
dds = DeseqDataSet(counts=counts_df, metadata=metadata, design=design_matrix, quiet=True)
dds.deseq2()

contrast = np.zeros(design_matrix.shape[1])
contrast[design_matrix.columns.get_loc("condition_B")] = 1
stats = DeseqStats(dds, contrast=contrast, quiet=True)
stats.summary()
```

## Fitting Options

- `fit_type="parametric"` is the default dispersion trend fit and broadly mirrors default DESeq2 behavior.
- `fit_type="mean"` uses the mean of gene-wise dispersion estimates; use it when parametric trend fitting is unsuitable or a user explicitly requests the mean fit.
- `size_factors_fit_type="ratio"` is the default median-of-ratios normalization. When every gene has at least one zero, PyDESeq2 warns and switches to iterative size factors. Use `"poscounts"` or `"iterative"` deliberately when the data are zero-heavy and the user requests that behavior.
- `low_memory=True` removes intermediate arrays such as Cook's distances when they are no longer needed, which is useful for wide datasets.
- `refit_cooks=True` is the default and attempts Cook's outlier replacement/refit when enough replicate samples are available.
- `min_replicates=7` controls the minimum replicate count required for replacement during Cook's refit.

## CPU and Inference Choices

Always bound CPUs in scripts and automation:

```python
inference = DefaultInference(n_cpus=1, batch_size=128, joblib_verbosity=0, backend="loky")
dds = DeseqDataSet(counts=counts_df, metadata=metadata, design="~condition", inference=inference)
stats = DeseqStats(dds, contrast=["condition", "B", "A"], inference=inference)
```

`n_cpus=None` uses all available CPUs. Avoid it unless the user explicitly approves broad CPU use.

## Export Patterns

Save result tables with pandas:

```python
stats.summary()
stats.results_df.to_csv("deseq_results.csv")
```

Save a fitted object only when requested. Prefer AnnData export over raw pickling of the `DeseqDataSet` object:

```python
adata = dds.to_picklable_anndata()
adata.write_h5ad("fitted_pydeseq2.h5ad")
```

If a user asks for LFC shrinkage or MA plots after `summary()`, route details to `../statistics-and-results/SKILL.md`; this sub-skill only covers the workflow handoff.
