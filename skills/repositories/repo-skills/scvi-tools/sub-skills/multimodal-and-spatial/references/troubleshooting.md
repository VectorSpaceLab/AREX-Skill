# Troubleshooting multimodal and spatial scvi-tools workflows

Start with the exact setup method and data keys. Most failures come from missing modality mappings, transformed data passed as counts, absent labels, or optional dependencies for external models.

## Setup fails with missing `modalities`

Symptoms:

- `ValueError: Modalities cannot be None.`
- Setup cannot find `rna_layer`, `protein_layer`, `atac_layer`, `sc_layer`, or `sp_layer`.

Fix:

1. Inspect `list(mdata.mod.keys())`.
2. Pass `modalities` using setup argument names, not generic labels:
   - `TOTALVI`: `{"rna_layer": "rna", "protein_layer": "protein"}`
   - `MULTIVI`: `{"rna_layer": "rna", "atac_layer": "atac", "protein_layer": "protein"}`
   - `Tangram`: `{"sc_layer": "sc", "sp_layer": "spatial", "density_prior_key": "spatial"}`
3. Verify every selected modality has the requested layer or usable `.X`.

## Count-data warnings or unstable training

Symptoms:

- Setup warns that data are not counts.
- Loss is `nan`, ELBO explodes, or posterior outputs are nonsensical.

Fix:

1. Use raw count layers for model setup, not log-normalized matrices.
2. Check nonnegativity and integer-like values in the selected layer.
3. For ATAC, binary accessibility is acceptable; for RNA/protein/methylation, counts should be count-like.
4. Reduce learning rate or train on a small subset only after data validation passes.

## `MULTIVI` gives unexpected missing-modality behavior

Symptoms:

- RNA-only or ATAC-only cells dominate the latent space.
- Protein outputs are absent or not useful.
- Imputation is requested but paired cells are too rare.

Fix:

1. Count cells by modality membership before setup.
2. Confirm paired multiome cells exist and are not lost due to barcode mismatch.
3. Use `TOTALVI` separately if the main requirement is RNA+protein denoising and ATAC is secondary.
4. Use `PEAKVI` separately for ATAC-only differential accessibility when no RNA+ATAC bridge exists.

## Protein panel mismatch in `TOTALVI`

Symptoms:

- Protein names or dimensions differ by batch.
- Missing proteins cause setup or model initialization errors.
- Denoised protein values are suspicious for batches without a panel.

Fix:

1. Ensure protein features are named consistently.
2. Use `panel_key` to identify antibody panels when panels vary.
3. Use `override_missing_proteins=True` only when missing panels are expected and documented.
4. Inspect normalized protein output by batch and panel before interpreting differential protein results.

## Spatial deconvolution has no reference labels

Symptoms:

- User asks for Stereoscope deconvolution but `sc_adata.obs` has no cell-type column.
- `RNAStereoscope.setup_anndata(..., labels_key=...)` fails.

Fix:

1. Do not fabricate labels from clusters without user approval.
2. Ask for a valid reference `labels_key` or run a separate annotation workflow first.
3. If labels are not available, choose `Tangram` for mapping rather than Stereoscope deconvolution.
4. Before training, intersect genes between single-cell and spatial data and record how many genes remain.

## Gene or peak feature mismatch

Symptoms:

- Query loading fails for `PEAKVI.load_query_data` or `MULTIVI.load_query_data`.
- Spatial model performance is poor despite successful setup.
- Feature dimensions mismatch between reference and target.

Fix:

1. Align features by names before setup; do not rely on positional order after subsetting.
2. Preserve reference feature order when constructing query matrices.
3. For spatial workflows, subset to shared genes with adequate expression in both modalities.
4. For ATAC query mapping, use the same peak set or a deliberate peak harmonization step.

## Optional external model import fails

Symptoms:

- Importing an external model works, but training fails due to `pyro`, genomic sequence, or plotting dependencies.
- `SCBASSET`, `Decipher`, or spatial utilities fail at runtime.

Fix:

1. Check the specific import path and optional package before committing to the workflow.
2. Run a tiny setup and one-epoch smoke test on copied data.
3. If optional extras are unavailable, provide a fallback model from core `scvi.model` when scientifically appropriate.
4. Do not install heavy extras or GPU packages without explicit user approval.

## Velocity layer errors in `VELOVI`

Symptoms:

- `spliced` or `unspliced` layer is missing.
- Layer shapes differ, contain negative values, or come from inconsistent preprocessing.

Fix:

1. Confirm `adata.layers["spliced"]` and `adata.layers["unspliced"]` exist.
2. Check both layers match `adata.shape` and contain nonnegative normalized expression values.
3. Re-run RNA velocity preprocessing upstream if layers are raw/normalized inconsistently, filtered inconsistently, or empty.

## Methylation layer errors

Symptoms:

- `METHYLVI` or `METHYLANVI` setup fails on layer names.
- Coverage values are lower than methylated counts.

Fix:

1. Confirm every `methylation_contexts` modality has the requested `mc_layer` and `cov_layer`.
2. Check `mc <= cov` where coverage is positive in each methylation context.
3. Remove features or cells with zero coverage only if that matches the analysis plan.
4. Use `METHYLANVI` only when `labels_key` and `unlabeled_category` are well-defined.

## Contrastive or perturbation design is confounded

Symptoms:

- `ContrastiveVI` target/background groups also differ by batch or donor.
- `MRVI` sample keys have too few cells per condition.
- `SysVI` removes biological signal.

Fix:

1. Cross-tabulate group, batch, donor, sample, and condition columns before setup.
2. Balance or subset groups where possible.
3. Include covariates during setup only when the model supports them and the covariate is not the signal of interest.
4. Report design confounding instead of treating model output as causal.

## Safe smoke-test pattern

Use a copied subset before full training:

```python
subset = adata[: min(200, adata.n_obs)].copy()
# run the same setup call on subset
model = ModelClass(subset)
model.train(max_epochs=1, train_size=0.8, validation_size=0.2)
```

For `MuData`, subset observations consistently across modalities and call `mdata.update()` before setup. Keep smoke tests small on CPU; multimodal models are designed for GPU-scale training but should still validate setup on small data.
