# Annotation and Query Workflows

These workflows assume `import scvi`, an `AnnData` object with count data, and scvi-tools 1.4.x APIs.

## SCANVI semi-supervised annotation

Use `SCANVI` when known labels are available for reference cells and unlabeled/query cells share the same gene space.

1. Normalize metadata before setup:
   - Ensure `adata.obs[labels_key]` exists for every cell.
   - Choose a single string token for unknown cells, such as `"Unknown"` or `"unlabeled"`.
   - Convert labels to strings or categorical values consistently before setup.
2. Register the data:
   - `scvi.model.SCANVI.setup_anndata(adata, labels_key="cell_type", unlabeled_category="Unknown", batch_key="batch")`.
   - Include `layer=...` if raw counts are stored outside `adata.X`.
   - Include `size_factor_key=...`, `categorical_covariate_keys=...`, or `continuous_covariate_keys=...` only when they are part of the annotation design.
3. Train and predict:
   - `model = scvi.model.SCANVI(adata, linear_classifier=False)`.
   - `model.train(max_epochs=..., accelerator="auto", devices="auto")`.
   - `adata.obs["scanvi_label"] = model.predict()`.
   - For confidence, call `model.predict(soft=True)` when available in the installed version and store the maximum class probability separately.
4. Validate outputs:
   - Confirm `len(predictions) == adata.n_obs`.
   - Compare predicted labels on labeled cells against known labels before trusting query cells.
   - Flag low-confidence cells instead of forcing final annotations.

## Bootstrap SCANVI from a trained SCVI reference

Use `SCANVI.from_scvi_model(...)` when a trained `SCVI` model should provide the latent generative weights and `SCANVI` should add semi-supervised label prediction.

1. Train or load a compatible `SCVI` model:
   - `scvi.model.SCVI.setup_anndata(reference_adata, batch_key="batch", labels_key="cell_type")` if labels were known during setup.
   - `scvi_model = scvi.model.SCVI(reference_adata)` then `scvi_model.train(...)`.
2. Initialize SCANVI:
   - `scanvi = scvi.model.SCANVI.from_scvi_model(scvi_model, unlabeled_category="Unknown", labels_key="cell_type")`.
   - If the original `SCVI` was set up without labels, `labels_key` is required at this step.
   - If passing a new `adata`, it must validate against the trained `SCVI` registry: same genes, compatible layer, batch categories, and registered covariates.
3. Fine-tune and predict:
   - `scanvi.train(...)`.
   - `labels = scanvi.predict()` for hard labels.
   - Store hard labels, confidence, and the source model identifier in `adata.obs` or `adata.uns`.

## Query mapping cautions

For query/reference annotation, the query object must match the reference registry. Before calling `from_scvi_model(..., adata=query_adata)` or related query-loading APIs from other scvi-tools model classes:

- Reindex query genes to the reference `var_names`; missing genes should be handled deliberately, not silently reordered.
- Preserve the count layer name used by the reference setup.
- Map batch labels to known categories, or use query-extension workflows that explicitly support category extension.
- Keep the same `labels_key` column and `unlabeled_category` token in query data.
- Reject query labels that include new biological categories unless the task is open-set detection; SCANVI classifies into its registered label set.

## SOLO doublet detection

Use SOLO after training an `SCVI` model on count data. SOLO simulates doublets, embeds real and simulated cells through the trained model, then trains a classifier.

1. Register and train SCVI with supported fields:
   - `scvi.model.SCVI.setup_anndata(adata, batch_key="batch")` is supported.
   - Avoid extra categorical or continuous covariates for SOLO; `SOLO.from_scvi_model(...)` rejects them.
2. Create SOLO:
   - `solo = scvi.external.SOLO.from_scvi_model(scvi_model, doublet_ratio=2)`.
   - For multiple sequencing lanes or batches, prefer one SOLO run per lane: `SOLO.from_scvi_model(scvi_model, restrict_to_batch="batch_0")`.
3. Train and predict:
   - `solo.train(max_epochs=..., train_size=0.9, check_val_every_n_epoch=1)`.
   - `probs = solo.predict(soft=True)` returns probabilities with columns such as `"singlet"` and `"doublet"` for observed cells by default.
   - `calls = solo.predict(soft=False)` returns hard labels.
4. Call doublets:
   - Start with `probs["doublet"]` and choose a threshold appropriate to expected multiplet rate.
   - Save both continuous scores and thresholded calls.
   - Re-run per batch when chemistry, loading, or capture lanes differ.

## CellAssign marker-based assignment

Use CellAssign when a curated binary marker matrix defines cell types.

1. Build a marker matrix:
   - Rows are genes, indexed by gene names.
   - Columns are cell type labels.
   - Values are binary or numeric marker indicators compatible with a binary marker design.
   - Row index must be unique.
2. Align data and markers:
   - Subset and order data to marker genes: `bdata = adata[:, adata.var_names.isin(marker_df.index)].copy()`.
   - Then reorder markers exactly: `marker_df = marker_df.loc[bdata.var_names]`.
   - Reject empty marker columns and duplicated marker rows.
3. Register and train:
   - Compute a size factor, for example `adata.obs["size_factor"] = adata.X.sum(1) / adata.X.sum(1).mean()`.
   - `scvi.external.CellAssign.setup_anndata(bdata, size_factor_key="size_factor", batch_key="batch")`.
   - `model = scvi.external.CellAssign(bdata, marker_df)`.
   - `model.train(max_epochs=...)`.
4. Predict and audit:
   - `assignment_probs = model.predict()` returns a DataFrame with one column per marker-defined cell type.
   - Store `assignment_probs.idxmax(axis=1)` as hard labels and `assignment_probs.max(axis=1)` as confidence.
   - Inspect marker coverage and probability margins for closely related cell types.

## Combined annotation pattern

For production annotation, combine signals rather than blindly overwriting labels:

- Use SCANVI for reference label transfer.
- Use SOLO to remove or flag likely doublets before final differential analysis.
- Use CellAssign as an independent marker-based sanity check for major cell classes.
- Mark disagreements explicitly, for example `annotation_status = "review"` when SCANVI and CellAssign disagree or the top probability is low.
