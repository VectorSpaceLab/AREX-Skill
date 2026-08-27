# Downstream Troubleshooting

## Method Is Missing or Not Implemented

Symptom: `AttributeError: '<Model>' object has no attribute 'get_normalized_expression'` or a not-implemented error.

Fix:

1. Confirm the model family supports the requested downstream quantity: RNA models use `get_normalized_expression`, PEAKVI uses `get_normalized_accessibility`, methylation models use methylation-specific methods, and some topic/spatial/external models expose specialized accessors.
2. Use `dir(model)` or `hasattr(model, "differential_expression")` before writing generic utilities.
3. Route model selection/setup questions to the core or multimodal/spatial sub-skills rather than emulating unsupported outputs.

## Model Is Untrained

Symptom: downstream calls warn or fail because model training has not completed.

Fix:

1. Call `model.train(...)` before `get_latent_representation`, normalized accessors, differential tests, posterior predictive sampling, or criticism.
2. In notebooks, ensure the variable points to the trained instance, not a newly constructed model.
3. If the model was loaded from disk, validate it by running a small `get_latent_representation(indices=[0, 1])` smoke check before expensive analysis.

## Wrong Data Object or Registry Mismatch

Symptom: validation errors when passing a new `adata`/`mdata`, missing registry fields, or shape/key mismatches.

Fix:

1. Pass `adata=None` to use the model's original registered data when possible.
2. If passing a new object, ensure it has the same variables/modalities and setup keys used for the model class.
3. Re-run the correct class-level `setup_anndata` or `setup_mudata` only for compatible query/reference workflows; do not re-register an unrelated object and expect old model weights to match.
4. Check that count layers, protein `obsm`, region names, and MuData modalities still exist.

## Missing or Empty Groups

Symptom: differential methods fail, return empty results, or complain about only one category.

Fix:

1. Inspect `adata.obs[groupby].value_counts(dropna=False)` before calling `differential_expression`, `differential_accessibility`, or `differential_methylation`.
2. Verify `group1` and `group2` exactly match category values; integer-like strings and integers are distinct in pandas.
3. For query-string selections, test them first: `adata.obs.query("labels == 'label_1'").shape[0]`.
4. Avoid comparing groups after subsetting away one category; if using `adata[mask]`, confirm at least two groups remain.

## Missing Categories in Batch Conditioning

Symptom: `transform_batch`, `batchid1`, or `batchid2` fails or gives unexpected comparisons.

Fix:

1. Confirm the model was set up with a batch key; otherwise batch conditioning is unavailable.
2. Check category labels in the registered batch column and pass the same labels or valid integer codes.
3. For differential testing with `batch_correction=True`, provide compatible `batchid1` and `batchid2`; the shared differential engine handles same-batch comparisons, observed batches, or non-overlapping batch sets, but mixed partially overlapping sets may warn.
4. Use `transform_batch=None` to condition on observed batches when counterfactual normalization is not needed.

## Feature List Problems

Symptom: missing genes/regions/proteins, all-empty masks, or unexpected output columns.

Fix:

1. Compare requested genes with `adata.var_names`; compare regions with ATAC modality `var_names`; compare proteins with the registered protein names or protein modality `var_names`.
2. For posterior predictive RNA sampling, at least one `gene_list` entry must match or the method raises a value error.
3. Use small explicit lists for memory-heavy calls, then expand once the feature names are validated.
4. Preserve original feature names through preprocessing; downstream accessors generally use registered feature order.

## Memory or Runtime Is Too High

Symptom: normalized outputs, posterior predictive samples, feature correlations, or differential tests are slow or exhaust memory.

Fix:

1. Restrict cells with `indices` or pass a subset object for exploratory runs.
2. Restrict features with `gene_list`, `region_list`, or `protein_list`.
3. Lower `n_samples`, `n_samples_overall`, `mc_samples`, or `m_permutation` for initial checks.
4. Increase `batch_size` only if memory allows; otherwise reduce it to avoid device or RAM exhaustion.
5. Avoid full `get_feature_correlation_matrix` on thousands of features; it creates feature-by-feature matrices.

## Differential Results Look Biologically Implausible

Symptom: top features are dominated by low counts, batch artifacts, or missing groups.

Fix:

1. Confirm group labels and batch labels reflect the intended biological comparison.
2. Use `mode="change"`, tune `delta`, and inspect effect-size columns in addition to Bayes factors or probabilities.
3. For RNA/protein comparisons, check pseudocount behavior and protein-specific options such as `protein_prior_count`, `include_protein_background`, and `sample_protein_mixing`.
4. Consider `batch_correction=True` only when batch labels and biological groups are not confounded beyond interpretation.
5. Validate a few marker features manually against raw counts or normalized values.

## Criticism or Posterior Predictive Checks Fail

Symptom: `PosteriorPredictiveCheck` cannot construct samples, metrics fail, or criticism report output is incomplete.

Fix:

1. Use trained SCVI-like models that can generate posterior predictive samples for the same `adata` structure.
2. Start with small `indices` and low `n_samples` to validate the workflow.
3. Provide `label_key` or `de_groupby` only if that column exists and has enough cells per category.
4. Skip metrics that do not fit the data using `skip_metrics` in `create_criticism_report`.
5. Install optional plotting/report dependencies if report rendering fails while core model APIs work.

## Normalized Expression from the Wrong Family

Symptom: a workflow asks for `get_normalized_expression` on `PEAKVI`, methylation-only, topic, or accessibility-only models.

Fix:

1. Map the biological quantity to the model output: accessibility uses `get_normalized_accessibility`, methylation uses methylation-specific differential methods, topic models expose topic/latent methods, and cross-modality models may expose `get_imputed_values`.
2. If RNA expression is required, use a model trained with RNA input or a multimodal model with an RNA decoder.
3. Do not treat missing methods as interchangeable; downstream outputs are tied to the likelihood and registered modality.
