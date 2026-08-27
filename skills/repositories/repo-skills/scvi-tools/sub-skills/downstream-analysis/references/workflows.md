# Downstream Analysis Workflows

## Preflight Checks

1. Confirm the model has been trained before calling posterior accessors: `model.train(...)` should already have completed.
2. Confirm the analysis data is registered for the same model family. If passing a new `adata` or `mdata`, it must have equivalent structure to the training object and compatible setup fields.
3. Check method availability with `hasattr(model, "method_name")`; downstream APIs vary by model family and modality.
4. Check observation categories before group comparisons: `adata.obs[groupby].value_counts(dropna=False)` and verify `group1`, `group2`, or query-string selections are non-empty.
5. Keep first runs small with `indices`, `gene_list`, `region_list`, `protein_list`, `batch_size`, or lower posterior sample counts, then scale up.

## Latent Representations

Most VAE-style models expose:

```python
latent = model.get_latent_representation(adata=None, indices=None, give_mean=True, batch_size=None)
adata.obsm["X_scvi"] = latent
```

Use `return_dist=True` when you need posterior mean and variance for uncertainty-aware analysis:

```python
qz_mean, qz_var = model.get_latent_representation(return_dist=True)
```

For `MULTIVI`, choose the embedding space explicitly with `modality="joint"`, `modality="expression"`, or `modality="accessibility"`. For MRVI-style models, use their model-specific arguments such as `use_mean` and `give_z` rather than assuming the generic VAE signature.

Typical follow-up steps are nearest-neighbor graph construction, UMAP, Leiden clustering, trajectory tools, or batch-effect visualization. These plotting and clustering packages are optional extras in many installations; install scanpy support separately when needed.

## Normalized Expression, Protein, and Accessibility

For RNA models such as `SCVI`, `SCANVI`, `AUTOZI`, and `LinearSCVI`:

```python
expr = model.get_normalized_expression(
    adata=None,
    indices=None,
    transform_batch=None,
    gene_list=["CD3D", "MS4A1"],
    library_size=1,
    n_samples=1,
    return_mean=True,
    return_numpy=False,
)
```

Interpret `get_normalized_expression` as decoded normalized expression, not raw counts. Use `library_size="latent"` only when the model supports and you want latent-library scaling; use a numeric `library_size` for comparable expression magnitudes across cells. Use `transform_batch="batch_a"` or a list of batch categories for counterfactual batch conditioning when the model was registered with a batch key.

For `TOTALVI`, `get_normalized_expression` can return RNA and protein values and accepts `gene_list`, `protein_list`, `sample_protein_mixing`, `scale_protein`, and `include_protein_background`. Use `get_protein_foreground_probability(...)` when the biological question is foreground protein signal rather than expression magnitude.

For `PEAKVI` and `MULTIVI`, use `get_normalized_accessibility(...)` with `region_list`, `threshold`, `normalize_cells`, and `normalize_regions`. A non-`None` `threshold` turns probabilities into binary accessibility calls; keep it `None` for continuous posterior accessibility estimates.

## Imputation-Like and Posterior Predictive Outputs

Use normalized accessors for denoising or imputation-like downstream matrices. They infer expected decoded values from the posterior and are usually preferable to raw posterior predictive samples for downstream ranking or visualization.

Use posterior predictive sampling when you need generated observations from the model likelihood:

```python
x_hat = model.posterior_predictive_sample(n_samples=3, gene_list=["CD3D"], batch_size=128)
```

RNA models return sparse multidimensional samples. `TOTALVI.posterior_predictive_sample(...)` can sample genes and proteins. These samples are stochastic and can be memory-heavy, so restrict features and cells for exploratory checks.

External models may have specialized imputation methods, for example `get_imputed_values(...)` on models designed for cross-modality imputation. Prefer the model-specific method name documented by the class over forcing `get_normalized_expression` onto an unsupported family.

## Differential Expression and Related Tests

Generic RNA-style differential expression:

```python
de = model.differential_expression(
    adata=None,
    groupby="cell_type",
    group1="B cells",
    group2="T cells",
    mode="change",
    delta=0.25,
    fdr_target=0.05,
    batch_correction=False,
)
```

Selection options:

- `groupby`, `group1`, `group2`: compare categories in `adata.obs[groupby]`; omit `group2` to compare `group1` against the rest.
- `idx1`, `idx2`: pass boolean masks, integer indices, or pandas query strings such as `"labels == 'label_1'"` for precise subsets.
- `batch_correction=True` with `batchid1` and `batchid2`: compare posterior values conditioned on specified batches rather than observed batches.
- `mode="vanilla"`: Bayes-factor style test from normalized means.
- `mode="change"`: effect-size test using `delta`, pseudocounts, and posterior log-fold changes.

For `TOTALVI`, `differential_expression` can include proteins; tune `protein_prior_count`, `scale_protein`, `sample_protein_mixing`, `include_protein_background`, and `use_field` for protein/RNA behavior. For `MULTIVI`, use `differential_expression(...)` for RNA and `differential_accessibility(...)` for ATAC. For `PEAKVI`, use `differential_accessibility(...)` with `region_list`-like post-filtering of results when needed. For methylation models, use `differential_methylation(...)` with `two_sided=True` unless the biological question is directional.

## Differential Abundance

VAE-style models that inherit the abundance mixin expose:

```python
da = model.differential_abundance(
    adata=adata,
    adata_sub=None,
    sample_key="sample",
    batch_size=128,
    num_cells_posterior=100,
    dof=3,
)
```

The method estimates sample-specific aggregate posteriors and stores log probabilities in `adata.obsm["da_log_probs"]` or `adata_sub.obsm["da_log_probs"]`. Use a `sample_key` with real biological samples or donors, not cluster labels, unless the task explicitly asks for cluster-level abundance scoring. Set `num_cells_posterior` to cap per-sample posterior cells for large datasets.

Some models intentionally do not implement differential abundance. If a method raises a not-implemented error, route to a supported VAE-style model or use a dedicated abundance workflow outside this sub-skill.

## Feature Correlations

RNA models and `TOTALVI` expose `get_feature_correlation_matrix(...)`:

```python
corr = model.get_feature_correlation_matrix(
    n_samples=10,
    correlation_type="spearman",
    transform_batch=None,
)
```

Use `correlation_type="spearman"` for rank-based relationships and `"pearson"` for linear relationships. Increase `n_samples` for more stable uncertainty-aware correlations, but expect quadratic memory growth with the number of features.

## Posterior Predictive Checks and Criticism

`scvi.criticism` provides posterior predictive checks for comparing one or more trained SCVI-like models:

```python
from scvi.criticism import PosteriorPredictiveCheck, create_criticism_report

models = {"baseline": model_a, "covariate_model": model_b}
ppc = PosteriorPredictiveCheck(adata, models, n_samples=5, indices=None)
ppc.coefficient_of_variation("cells")
ppc.coefficient_of_variation("features")
ppc.zero_fraction()
ppc.calibration_error()
ppc.differential_expression(de_groupby="cell_type", p_val_thresh=0.05)

create_criticism_report(model_a, adata=adata, n_samples=5, label_key="cell_type", save_folder="report")
```

Use criticism for model quality assessment, not for routine marker discovery. Important outputs include cell-wise and feature-wise coefficient of variation, zero fraction preservation, calibration, and differential-expression agreement. If a cell-wise coefficient-of-variation score is poor, generated expression may be unsuitable for downstream analysis even when the latent representation remains useful.
