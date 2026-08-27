# Downstream API Reference

This reference lists common downstream methods in scvi-tools 1.4.x. Always inspect the live object with `type(model)` and `hasattr` because specialized external models may override signatures.

## Common VAE Accessors

- `model.get_latent_representation(adata=None, indices=None, give_mean=True, mc_samples=5000, batch_size=None, return_dist=False, dataloader=None, **data_loader_kwargs)` returns an array with shape `(n_obs, n_latent)`; with `return_dist=True`, returns `(qz_mean, qz_var)`.
- `model.differential_abundance(adata=None, adata_sub=None, sample_key=None, batch_size=128, num_cells_posterior=None, dof=None, dataloader=None)` returns/stores sample log probabilities; for AnnData/MuData input, results are in `.obsm["da_log_probs"]`.

Supported abundance families include common VAE-style RNA, protein, and multimodal models. `AmortizedLDA` intentionally raises not implemented for differential abundance.

## RNA-Style Methods

Methods inherited by RNA-seq model families such as `SCVI`, `SCANVI`, `AUTOZI`, and `LinearSCVI`:

- `get_normalized_expression(adata=None, indices=None, transform_batch=None, gene_list=None, library_size=1, n_samples=1, n_samples_overall=None, weights=None, batch_size=None, return_mean=True, return_numpy=None, silent=True, dataloader=None, data_loader_kwargs=None, **importance_weighting_kwargs)` returns a `pandas.DataFrame` by default when possible, otherwise a NumPy array.
- `differential_expression(adata=None, groupby=None, group1=None, group2=None, idx1=None, idx2=None, mode="vanilla", delta=0.25, batch_size=None, all_stats=True, batch_correction=False, batchid1=None, batchid2=None, fdr_target=0.05, silent=False, weights="uniform", filter_outlier_cells=False, importance_weighting_kwargs=None, dataloader=None, **kwargs)` returns a `pandas.DataFrame` with differential statistics.
- `posterior_predictive_sample(adata=None, indices=None, transform_batch=None, n_samples=1, gene_list=None, batch_size=None, dataloader=None, silent=True, **data_loader_kwargs)` returns sparse posterior predictive samples.
- `get_feature_correlation_matrix(adata=None, indices=None, n_samples=10, batch_size=64, rna_size_factor=1000, transform_batch=None, correlation_type="spearman", silent=True)` returns a gene-gene correlation `DataFrame`.

Important return-shape rules for `get_normalized_expression`:

- `n_samples=1` or `return_mean=True`: 2-D cells by genes.
- `n_samples>1` and `return_mean=False`: 3-D samples by cells by genes and forces NumPy output.
- `n_samples_overall` samples posterior values across cells and returns sampled rows by genes.

## TOTALVI Methods

`TOTALVI` adds protein-aware downstream outputs:

- `get_normalized_expression(adata=None, indices=None, n_samples_overall=None, transform_batch=None, gene_list=None, protein_list=None, library_size=1, n_samples=1, sample_protein_mixing=False, scale_protein=False, include_protein_background=False, batch_size=None, return_mean=True, return_numpy=None, silent=True)` returns normalized RNA/protein estimates.
- `get_protein_foreground_probability(adata=None, indices=None, transform_batch=None, protein_list=None, n_samples=1, batch_size=None, return_mean=True, return_numpy=None, silent=True)` returns protein foreground probabilities.
- `differential_expression(..., mode="change", delta=0.25, protein_prior_count=0.1, scale_protein=False, sample_protein_mixing=False, include_protein_background=False, use_field=None, pseudocounts=1e-05, **kwargs)` supports differential testing over RNA/protein fields.
- `posterior_predictive_sample(adata=None, indices=None, n_samples=1, batch_size=None, gene_list=None, protein_list=None)` samples posterior predictive RNA/protein observations.
- `get_feature_correlation_matrix(..., correlation_type="spearman", log_transform=False, silent=True)` supports uncertainty-aware feature correlations.

## PEAKVI and MULTIVI Accessibility

`PEAKVI`:

- `get_normalized_accessibility(adata=None, indices=None, n_samples_overall=None, region_list=None, transform_batch=None, use_z_mean=True, threshold=None, normalize_cells=False, normalize_regions=False, batch_size=128, return_numpy=False, dataloader=None)` returns accessibility probabilities or thresholded calls.
- `differential_accessibility(adata=None, groupby=None, group1=None, group2=None, idx1=None, idx2=None, mode="change", delta=0.05, batch_size=None, all_stats=True, batch_correction=False, batchid1=None, batchid2=None, fdr_target=0.05, silent=False, dataloader=None, **kwargs)` returns region-level differential accessibility statistics.

`MULTIVI`:

- `get_latent_representation(adata=None, modality="joint", indices=None, give_mean=True, batch_size=None, return_dist=False, dataloader=None)` returns joint, expression-only, or accessibility-only latent representations.
- `get_normalized_expression(..., gene_list=None, use_z_mean=True, n_samples=1, return_mean=False, return_numpy=False, silent=True)` returns RNA estimates.
- `get_normalized_accessibility(..., region_list=None, threshold=None, normalize_cells=False, normalize_regions=False, return_numpy=False)` returns ATAC estimates.
- `differential_expression(..., mode="change", delta=0.25, pseudocounts=1e-06, **kwargs)` and `differential_accessibility(..., mode="change", delta=0.05, pseudocounts=1e-06, **kwargs)` cover modality-specific tests.
- `get_protein_foreground_probability(..., protein_list=None, use_z_mean=True, return_mean=True, return_numpy=None, silent=True)` is available for protein-aware MULTIVI configurations.

## Methylation and MRVI-Style Methods

Methylation models expose `differential_methylation(mdata=None, groupby=None, group1=None, group2=None, idx1=None, idx2=None, mode="vanilla", delta=0.05, batch_size=None, all_stats=True, batch_correction=False, batchid1=None, batchid2=None, fdr_target=0.05, silent=False, two_sided=True, **kwargs)`.

MRVI-style models use specialized downstream APIs:

- `get_latent_representation(adata=None, indices=None, batch_size=None, use_mean=True, give_z=False, dataloader=None)`.
- `differential_abundance(adata=None, sample_cov_keys=None, sample_subset=None, compute_log_enrichment=False, omit_original_sample=True, batch_size=128)`.
- `differential_expression(adata=None, sample_cov_keys=None, sample_subset=None, batch_size=128, use_vmap="auto", normalize_design_matrix=True, add_batch_specific_offsets=False, mc_samples=50, store_lfc=False, store_lfc_metadata_subset=None, store_baseline=False, eps_lfc=0.0001, filter_inadmissible_samples=False, lambd=0.0, delta=0.3, **filter_samples_kwargs)`.
- `get_normalized_expression(..., library_size="latent", return_mean=False, return_numpy=None, **importance_weighting_kwargs)`.

## Differential Result Interpretation

Common differential result columns vary by model and mode, but often include probabilities, Bayes factors, effect-size summaries such as log-fold change, raw means, nonzero proportions, and FDR-oriented flags. Treat `fdr_target` as a result-thresholding target, not a guarantee that categories were biologically valid. Sort and filter using both statistical columns and domain-specific effect sizes.

Use `all_stats=False` for lighter result tables when only top-ranked features are needed. Use `silent=True` in scripts and batch jobs to suppress progress output.

## Criticism API

- `scvi.criticism.PosteriorPredictiveCheck(adata, models, n_samples=..., indices=...)` creates a PPC object from a mapping such as `{"model_a": model_a, "model_b": model_b}`.
- `ppc.coefficient_of_variation("cells")` and `ppc.coefficient_of_variation("features")` populate cell-wise and feature-wise CV metrics.
- `ppc.zero_fraction()` checks zero preservation.
- `ppc.calibration_error(confidence_intervals=None)` checks calibration.
- `ppc.differential_expression(de_groupby=None, de_method="t-test", n_samples=1, cell_scale_factor=10000.0, p_val_thresh=0.05, n_top_genes_fallback=...)` compares differential-expression behavior.
- `scvi.criticism.create_criticism_report(model, adata=None, skip_metrics=(), n_samples=5, label_key=None, save_folder=None)` writes an HTML/report bundle for a trained model.
