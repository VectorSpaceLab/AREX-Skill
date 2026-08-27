# Model-Fitting Internals Reference

This reference covers PyDESeq2 0.5.4 internals for agents that need to step through a fit, inspect intermediate state, or debug low-level behavior.

## Core Objects

Use `DeseqDataSet` for count modeling. It subclasses `AnnData`, so fitted state is stored in AnnData containers:

| Container | Typical PyDESeq2 keys | Meaning |
|---|---|---|
| `X` | raw count matrix | Samples by genes integer counts. |
| `obs` | design columns, `size_factors`, `replaceable` | Sample-level metadata and fitted sample factors. |
| `var` | `_normed_means`, `non_zero`, `_MoM_dispersions`, `genewise_dispersions`, `fitted_dispersions`, `MAP_dispersions`, `dispersions`, convergence flags, outlier/refit flags | Gene-level fitted quantities. |
| `layers` | `normed_counts`, `_mu_hat`, `_vst_mu_hat`, `cooks`, `replace_cooks`, `vst_counts` | Matrix-valued intermediates aligned to `X`. |
| `obsm` | `design_matrix`, `_mu_LFC`, `_hat_diagonals`, temporary `design_matrix_buffer` | Sample-aligned matrices and temporary fitting buffers. |
| `varm` | `LFC` | Gene by design-coefficient fitted log fold changes on natural-log scale. |
| `uns` | `trend_coeffs`, `vst_trend_coeffs`, `disp_function_type`, `mean_disp`, `_squared_logres`, `prior_disp_var` | Unstructured fit configuration and trend/prior parameters. |

Use `to_picklable_anndata()` when a future agent needs a picklable AnnData copy; it converts the stored design matrix to a plain DataFrame.

## Staged DEA Fitting Order

`DeseqDataSet.deseq2(fit_type=None)` is a wrapper over these stages:

1. `fit_size_factors(fit_type=size_factors_fit_type, control_genes=control_genes)`
2. `fit_genewise_dispersions()`
3. `fit_dispersion_trend()`
4. `fit_dispersion_prior()`
5. `fit_MAP_dispersions()`
6. `fit_LFC()`
7. `calculate_cooks()`
8. `refit()` when `refit_cooks=True`
9. `cooks_outlier()` to compute the Cooks p-value filtering mask for downstream statistics

Manual calls are resilient in many cases: later stages often call prerequisites if their expected keys are absent. For transparent debugging, still call stages in order and inspect keys after each step.

## Stage Details

### `fit_size_factors(fit_type=None, control_genes=None)`

Fits sample-wise normalization factors.

- Default `fit_type=None` uses `dds.size_factors_fit_type` from construction.
- Valid size-factor modes are `"ratio"`, `"poscounts"`, and `"iterative"`.
- `control_genes` may be any valid AnnData gene indexer: boolean mask, integer positions, gene-name strings, or a pandas index.
- Stores `dds.obs["size_factors"]`, `dds.layers["normed_counts"]`, and `dds.var["_normed_means"]`.
- Ratio and poscounts modes also set `dds.logmeans` and `dds.filtered_genes`; iterative mode leaves `dds.logmeans` unavailable for leakage-safe external transforms.
- If every gene contains at least one zero, ratio mode warns and switches to iterative mode.

### `fit_genewise_dispersions(vst=False)`

Fits independent negative-binomial dispersion estimates for non-all-zero genes.

- Calls `fit_size_factors()` if `dds.obs["size_factors"]` is missing.
- Marks non-all-zero genes in `dds.var["non_zero"]`, `dds.non_zero_idx`, and `dds.non_zero_genes`.
- Fits rough/method-of-moments initial dispersions into `dds.var["_MoM_dispersions"]`.
- Stores fitted means in `dds.layers["_mu_hat"]` for DEA or `dds.layers["_vst_mu_hat"]` for VST.
- Stores `dds.var["genewise_dispersions"]` for DEA or `dds.var["vst_genewise_dispersions"]` for VST.
- Stores optimizer convergence in `dds.var["_genewise_converged"]`.

### `fit_dispersion_trend(vst=False)`

Fits the dispersion-mean curve.

- Uses `dds.fit_type` for DEA or `dds.vst_fit_type` for VST.
- Valid trend fit types are `"parametric"` and `"mean"`.
- Parametric mode fits `a0 + a1 / mean` via a gamma-family GLM; if convergence fails or coefficients become invalid, PyDESeq2 warns and falls back to mean trend.
- DEA parametric mode stores `dds.uns["trend_coeffs"]`, `dds.uns["disp_function_type"] = "parametric"`, and `dds.var["fitted_dispersions"]`.
- DEA mean mode stores `dds.uns["mean_disp"]`, `dds.uns["disp_function_type"] = "mean"`, and constant `dds.var["fitted_dispersions"]`.
- VST parametric mode stores `dds.uns["vst_trend_coeffs"]`; VST mean mode sets `dds.vst_fit_type = "mean"` and uses `dds.var["vst_genewise_dispersions"]` during transform.

### `fit_dispersion_prior()`

Computes the dispersion prior variance used for MAP shrinkage.

- Calls `fit_dispersion_trend()` if `dds.var["fitted_dispersions"]` is absent.
- Uses log residuals between `genewise_dispersions` and `fitted_dispersions` for non-zero genes.
- Warns when residual degrees of freedom (`n_samples - n_design_columns`) is less than or equal to 3.
- Stores `dds.uns["_squared_logres"]` and `dds.uns["prior_disp_var"]`.

### `fit_MAP_dispersions()`

Fits posterior dispersion estimates and chooses final dispersions.

- Calls `fit_dispersion_prior()` if `dds.uns["prior_disp_var"]` is absent.
- Uses `dds.layers["_mu_hat"]`, `dds.var["fitted_dispersions"]`, and `dds.uns["prior_disp_var"]`.
- Stores `dds.var["MAP_dispersions"]`, `dds.var["_MAP_converged"]`, and final `dds.var["dispersions"]`.
- Marks `dds.var["_outlier_genes"]`; these genes keep `genewise_dispersions` instead of MAP-shrunk dispersions.
- With `low_memory=True`, deletes `dds.layers["_mu_hat"]` after MAP fitting.

### `fit_LFC()`

Fits negative-binomial GLM coefficients.

- Calls `fit_MAP_dispersions()` if final `dds.var["dispersions"]` is absent.
- Stores natural-log coefficients in `dds.varm["LFC"]` with columns matching `dds.obsm["design_matrix"].columns`.
- Stores fitted means and leverage diagonals in `dds.obsm["_mu_LFC"]` and `dds.obsm["_hat_diagonals"]` for Cooks distance.
- Stores convergence flags in `dds.var["_LFC_converged"]`.

### `calculate_cooks()`

Computes Cook's distances for outlier detection.

- Requires final dispersions and LFC intermediates; normally call after `fit_LFC()`.
- Stores `dds.layers["cooks"]`.
- With `low_memory=True`, deletes `dds.obsm["_mu_LFC"]` and `dds.obsm["_hat_diagonals"]` after Cooks distances are computed.

### `refit()`

Replaces eligible Cooks outliers and refits affected genes.

- Calls internal outlier replacement using `dds.layers["cooks"]`.
- Uses `dds.min_replicates` to decide which samples are replaceable; default is 7.
- Stores `dds.obs["replaceable"]`, `dds.var["replaced"]`, and `dds.var["refitted"]`.
- For refitted genes, updates `_normed_means`, `LFC`, `genewise_dispersions`, `fitted_dispersions`, and `dispersions` from a sub-fit.
- Stores `dds.layers["replace_cooks"]` when genes are refitted.
- If no outliers are replaceable, `dds.var["refitted"]` is all false.

### `cooks_outlier()`

Determines which genes should have p-values filtered based on Cooks distances.

- Uses an F-distribution cutoff with design degrees of freedom.
- Uses only sample groups with at least 3 replicates for max-Cooks filtering.
- Stores and returns `dds.var["_pvalue_cooks_outlier"]`.
- With `low_memory=True`, may delete `dds.layers["cooks"]` and `dds.layers["replace_cooks"]`.

## Fit-Type Controls

`fit_type` controls dispersion trend fitting for DEA and, unless overridden, VST.

- `fit_type="parametric"`: fits a parametric curve `a0 + a1 / mean`; stores `trend_coeffs` for DEA or `vst_trend_coeffs` for VST.
- `fit_type="mean"`: uses a trimmed mean of genewise dispersions; stores `mean_disp` and constant fitted dispersions.
- `dds.deseq2(fit_type="mean")` changes `dds.fit_type` for the DEA fit.
- `dds.vst(fit_type="mean")` changes `dds.vst_fit_type` for VST only and should not change an already fitted DEA `dds.fit_type`.

## DefaultInference Behavior

`DefaultInference(joblib_verbosity=0, batch_size=128, n_cpus=None, backend="loky")` implements the default inference routines with NumPy/SciPy/scikit-learn and joblib.

High-level methods used by `DeseqDataSet` include:

- `lin_reg_mu()` for mean initialization in balanced design settings.
- `irls()` for negative-binomial GLM LFC fitting and some mean initialization paths.
- `alpha_mle()` for genewise and MAP dispersion optimization.
- `dispersion_trend_gamma_glm()` for parametric dispersion trend fitting.
- `wald_test()` and `lfc_shrink_nbinom_glm()` for downstream statistics and shrinkage.

CPU and backend guidance:

- If `inference` is omitted, `DeseqDataSet` creates `DefaultInference(n_cpus=n_cpus)`.
- If both `inference` and `n_cpus` are provided and the inference object has an `n_cpus` attribute, PyDESeq2 tries to override it.
- `n_cpus=None` resolves through PyDESeq2's process-count helper and may use all available CPUs; use `n_cpus=1` for deterministic examples and constrained environments.
- `backend="loky"` is the default joblib process backend. Other joblib backends may be useful for specialized debugging, but should be chosen deliberately.

## Low-Memory Side Effects

`low_memory=True` reduces memory use by deleting intermediates once they are no longer needed by the high-level pipeline.

Expect these differences:

- After `fit_MAP_dispersions()`, `dds.layers["_mu_hat"]` may be absent.
- After `calculate_cooks()`, `dds.obsm["_mu_LFC"]` and `dds.obsm["_hat_diagonals"]` may be absent.
- After `cooks_outlier()`, `dds.layers["cooks"]` and `dds.layers["replace_cooks"]` may be absent.

If a user wants to inspect internals after each stage, set `low_memory=False` and use a small count matrix.

## Minimal Stepwise Pattern

```python
from pydeseq2.dds import DeseqDataSet
from pydeseq2.default_inference import DefaultInference

dds = DeseqDataSet(
    counts=counts_df,
    metadata=metadata_df,
    design="~condition",
    inference=DefaultInference(n_cpus=1),
    quiet=True,
)

dds.fit_size_factors()
dds.fit_genewise_dispersions()
dds.fit_dispersion_trend()
dds.fit_dispersion_prior()
dds.fit_MAP_dispersions()
dds.fit_LFC()
dds.calculate_cooks()
if dds.refit_cooks:
    dds.refit()
dds.cooks_outlier()
```

Use `scripts/inspect_stepwise_pipeline.py` for a runnable, self-contained version that prints key presence after every stage.
