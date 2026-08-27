# Model-Fitting Internals Troubleshooting

Use this guide to map PyDESeq2 internals errors or warnings to the next staged action.

## `vst_transform` Fails Before `vst_fit`

Symptom:

```text
RuntimeError: The vst_fit method should be called prior to vst_transform.
```

Cause: `dds.obs["size_factors"]`, `dds.layers["normed_counts"]`, and VST trend state have not been fitted.

Fix:

```python
dds.vst_fit(use_design=False)
transformed = dds.vst_transform()
```

For external counts, fit on training data first:

```python
train_dds.vst_fit(use_design=False)
test_vst = train_dds.vst_transform(test_counts.to_numpy())
```

## Missing Dispersion Curve Before VST Transform

Symptom:

```text
RuntimeError: Fit the dispersion curve prior to applying VST.
```

Cause: Parametric VST transform needs `dds.uns["vst_trend_coeffs"]`, but the VST dispersion trend was not fitted or was removed from state.

Fix:

- Run `dds.vst_fit(use_design=False)` or `dds.vst(use_design=False)` before `vst_transform()`.
- If using manual internals, fit VST genewise dispersions and parametric VST trend before transforming.
- Inspect `dds.uns.keys()` for `"vst_trend_coeffs"` when `dds.vst_fit_type == "parametric"`.

## Every Gene Has a Zero Count

Symptom:

```text
Every gene contains at least one zero, cannot compute log geometric means. Switching to iterative mode.
```

Cause: Ratio size factors require at least some genes with finite log geometric means. If every gene has at least one zero across samples, PyDESeq2 cannot compute ratio logmeans.

Fix options:

- Accept iterative fitting for the current dataset when this is the intended sparse-count behavior.
- Try `size_factors_fit_type="poscounts"` for sparse positive-count settings where positive-only geometric means are appropriate.
- Filter genes with extremely sparse or all-zero counts before fitting if scientifically valid.
- In train/test settings, do not rely on iterative size factors for leakage-safe external normalization; use ratio fit/transform when possible or report that leakage-free VST is not available for that sparse split.

## Invalid `fit_type`

Symptoms:

```text
Expected 'parametric' or 'mean' trend curve fit types, received ...
Found fit_type '...'. Expected 'parametric' or 'mean'.
```

Cause: DEA and VST dispersion trends only support `"parametric"` and `"mean"`.

Fix:

- Use `DeseqDataSet(..., fit_type="parametric")` or `fit_type="mean"`.
- Use `dds.deseq2(fit_type="mean")` only when intentionally changing the DEA fit type.
- Use `dds.vst(fit_type="mean")` to change VST behavior without changing an already fitted DEA `dds.fit_type`.

## Invalid `size_factors_fit_type`

Symptom: later stages fail or produce confusing state because the size-factor mode is not recognized.

Cause: Size-factor fitting only has explicit branches for `"ratio"`, `"poscounts"`, and `"iterative"`.

Fix:

- Use `DeseqDataSet(..., size_factors_fit_type="ratio")`, `"poscounts"`, or `"iterative"`.
- If passing directly, call `dds.fit_size_factors(fit_type="ratio")` or one of the other two valid values.
- Prefer `ratio` for standard bulk RNA-seq and leakage-safe external transforms.

## Control-Gene Indexer Failures

Symptoms:

- Gene names are reported missing.
- Boolean masks have the wrong length.
- Integer positions select unexpected genes.
- Size factors look extreme after restricting to controls.

Cause: `control_genes` is normalized through AnnData gene-axis indexing and then intersected with usable genes for the selected size-factor mode.

Fix:

- Check that control gene names exactly match `dds.var_names`.
- For boolean masks, ensure `len(mask) == dds.n_vars` and the mask is ordered like `dds.var_names`.
- For integer positions, print `list(enumerate(dds.var_names))` before choosing indices.
- Use more than one stable control gene when possible.
- Remember that passing `control_genes` to `fit_size_factors()` overrides `dds.control_genes` for that call.

## Train/Test Leakage With Iterative Size Factors

Symptom:

```text
The size factors were fitted iteratively. They will be re-computed with the counts to be transformed. In a train/test setting with a downstream task, this would result in a leak of data from test to train set.
```

Cause: Iterative size factors do not provide reusable median-of-ratios `logmeans` for external counts. When external counts are passed to `vst_transform`, PyDESeq2 recomputes logmeans from those external counts.

Fix:

- For leakage-safe normalization, use `deseq2_norm_fit(train_counts)` and `deseq2_norm_transform(test_counts, logmeans, filtered_genes)` when ratio logmeans are available.
- For VST, fit `train_dds.vst_fit()` with ratio-compatible size factors and transform held-out counts using the fitted object.
- If data sparsity forces iterative mode, disclose that external VST transform is not leakage-safe under that split and ask whether to change filtering/splitting or accept recomputation.

## Residual Degrees of Freedom Warning

Symptom:

```text
As the residual degrees of freedom is less than 3, the distribution of log dispersions is especially asymmetric and likely to be poorly estimated by the MAD.
```

Cause: `n_samples - n_design_columns <= 3` during `fit_dispersion_prior()`.

Fix:

- Simplify the design if scientifically valid.
- Add more samples or reduce factor levels/interactions.
- Treat dispersion prior and downstream inference as unstable in the report.
- For a design-free transform task, consider `vst(use_design=False)` instead of full DEA.

## Parametric Trend Fallback Warning

Symptom:

```text
The dispersion trend curve fitting did not converge. Switching to a mean-based dispersion trend.
```

Cause: The gamma GLM for the parametric dispersion trend did not converge or produced invalid coefficients.

Fix:

- Accept the fallback if the goal is a robust fit and document that `dds.uns["disp_function_type"]` became `"mean"`.
- Rerun with `fit_type="mean"` to make the choice explicit.
- Inspect `dds.var["genewise_dispersions"]` and `dds.var["_normed_means"]` for extreme genes.
- Consider filtering all-zero or very low-count genes before fitting if appropriate.

## `low_memory` Removed Expected Keys

Symptoms:

- `dds.layers["_mu_hat"]` missing after MAP dispersions.
- `dds.obsm["_mu_LFC"]` or `dds.obsm["_hat_diagonals"]` missing after Cooks distances.
- `dds.layers["cooks"]` missing after outlier filtering.

Cause: `DeseqDataSet(..., low_memory=True)` deletes intermediates after they are consumed.

Fix:

- Recreate the fit with `low_memory=False` when the user needs to inspect internals.
- Inspect keys immediately after each stage in a stepwise run.
- Do not assume low-memory objects contain all debug matrices after `deseq2()` completes.

## Cooks Refit Did Not Happen

Symptoms:

- `dds.var["replaced"]` is all false.
- `dds.var["refitted"]` is all false.
- No `replace_cooks` layer appears.

Likely causes:

- `refit_cooks=False`.
- No Cooks distances exceed the cutoff.
- No design groups have at least `min_replicates` replaceable samples; default is 7.
- Replacement would make affected genes all zero.

Fix:

- Check `dds.refit_cooks`, `dds.min_replicates`, `dds.obs["replaceable"]`, `dds.layers.get("cooks")`, `dds.var["replaced"]`, and `dds.var["refitted"]`.
- Explain that no refit can be a valid outcome for small cohorts or non-outlier synthetic data.

## Joblib, Backend, and CPU Surprises

Symptoms:

- The fit uses more cores than expected.
- Joblib logs are noisy.
- Process-based parallelism is slow or problematic in constrained containers.

Cause: `DefaultInference` uses joblib with `backend="loky"` by default and `n_cpus=None` may resolve to all available CPUs.

Fix:

```python
from pydeseq2.default_inference import DefaultInference

inference = DefaultInference(n_cpus=1, joblib_verbosity=0, backend="loky")
dds = DeseqDataSet(counts=counts_df, metadata=metadata_df, inference=inference)
```

Guidance:

- Use `n_cpus=1` for bundled scripts, examples, CI, and reproducible debugging.
- Increase `n_cpus` only after validating inputs and memory use.
- If passing a custom inference object, ensure it has an `n_cpus` attribute if the user expects `DeseqDataSet(..., n_cpus=...)` to override it.

## Full-Rank Design and Too Many Design Columns

Symptoms:

- Warning that the design matrix is not full rank.
- Error when fitting dispersions with too few residual degrees of freedom or equal sample/design dimensions.

Cause: Internals depend on a valid design matrix in `dds.obsm["design_matrix"]`.

Fix:

- Simplify formula terms, remove linearly dependent variables, or use a design-free VST if the task is only transformation.
- Keep `n_samples` comfortably larger than the number of design columns for DEA internals.
- Route detailed input/design validation to `../data-io-validation/SKILL.md` when the problem is schema construction rather than internals inspection.
