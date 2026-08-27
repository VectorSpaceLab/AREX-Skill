# Core Model Troubleshooting

## Missing `setup_anndata` Before Model Initialization

Symptoms:

- `AnnData` is not registered for the model.
- A model constructor fails immediately after `model = SCVI(adata)` or similar.
- The error mentions an `AnnDataManager`, registry, missing setup method, or mismatched setup class.

Recovery:

1. Identify the exact model class being constructed.
2. Call that class's `setup_anndata` on the same AnnData object before construction.
3. Use only keys that exist on the object: `adata.layers`, `adata.obs`, `adata.obsm`, and `adata.uns`.
4. Re-run setup after copying/subsetting if variables, layers, or relevant obs/obsm keys changed.

Example:

```python
from scvi.model import SCVI

assert "counts" in adata.layers
assert "batch" in adata.obs
SCVI.setup_anndata(adata, layer="counts", batch_key="batch")
model = SCVI(adata)
```

Do not fix a setup failure by switching model classes unless the user's modality or task actually changed.

## Wrong Model for the Modality

Symptoms:

- Protein keys passed to `SCVI.setup_anndata` fail because `protein_expression_obsm_key` is unsupported.
- ATAC/accessibility data is modeled as RNA expression and downstream accessibility methods are missing.
- A spatial deconvolution task tries to initialize `DestVI` directly without a `CondSCVI` reference model.

Recovery:

- RNA-only integration: `SCVI`, `LinearSCVI`, or `AUTOZI`.
- RNA with labels/unlabeled cells: `SCANVI`.
- RNA + protein/CITE-seq: `TOTALVI` with `protein_expression_obsm_key`.
- ATAC-only: `PEAKVI`.
- RNA + ATAC, including paired/unpaired mosaic data: `MULTIVI`.
- Spatial deconvolution from single-cell reference: train `CondSCVI` first, then call `DestVI.from_rna_model`.

## Missing or Misspelled Keys

Validate keys before setup:

```python
required_obs = ["batch", "cell_type"]
missing_obs = [key for key in required_obs if key not in adata.obs]
assert not missing_obs, missing_obs
assert "counts" in adata.layers
assert "protein_expression" in adata.obsm
```

Model-specific checks:

- `SCANVI`: `labels_key` and `unlabeled_category` are required. Verify `unlabeled_category in adata.obs[labels_key].astype(str).unique()`.
- `TOTALVI`: verify `adata.obsm[protein_expression_obsm_key]` is a 2D cells-by-proteins matrix with `adata.n_obs` rows.
- `MULTIVI`: if feature split cannot be inferred, pass `n_genes` and `n_regions` to the constructor.
- `PEAKVI`: verify the selected matrix contains accessibility counts/binary observations, not RNA-normalized values.
- `CondSCVI`: verify `labels_key` points to the cell-type labels intended for the reference model.

## Non-Count or Normalized Input

Symptoms:

- Training produces unstable losses or warnings about count data.
- Results look compressed because log-normalized expression was used as model input.

Recovery:

- Prefer raw counts in `adata.layers["counts"]` and pass `layer="counts"`.
- If only normalized data exists, ask the user for raw counts before writing a training workflow.
- Do not silently use `.X` if the docs or user mention that `.X` contains log-normalized values.

## Train Signature Mismatches

Symptoms:

- `TypeError: train() got an unexpected keyword argument ...`.
- `device` is accepted by Pyro models but not by regular PyTorch core models.
- `devices` is accepted by most Lightning-backed models but not the same as Pyro's singular `device` argument.

Recovery:

- Check [api-reference.md](api-reference.md) for the model-specific `train` signature.
- Use `scripts/inspect_model_api.py --model MODEL --json` against the installed version when in doubt.
- Keep optimizer options in `plan_kwargs` for Lightning/PyTorch models unless the model override exposes them directly, such as `lr` on `TOTALVI`, `PEAKVI`, `MULTIVI`, `CondSCVI`, or `DestVI`.

## Optional Dependency Failures

Symptoms:

- `ImportError` when using `AmortizedLDA` or Pyro-backed training.
- `ImportError` for `mlx` when importing or using `mlxSCVI`.
- CPU-only Torch is installed and GPU options fail.

Recovery:

- For `AmortizedLDA`, verify Pyro-related dependencies are installed before promising a runnable topic-model workflow.
- For `mlxSCVI`, verify the MLX package is installed and the environment is appropriate for Apple Silicon; otherwise use regular `SCVI`.
- If CPU-only Torch is present, set `accelerator="cpu"` or leave `accelerator="auto"` and avoid GPU-specific claims.
- Optional extras are not installed by default in a minimal scvi-tools installation; choose core PyTorch models when optional backends are unavailable.

## Save/Load and Class Mismatch

Symptoms:

- Loading an `mlxSCVI` checkpoint with `SCVI.load` fails, or the reverse.
- A loaded model reports AnnData schema mismatch.

Recovery:

- Load with the same class that saved the model.
- Pass compatible `adata` to `load(..., adata=adata)` when the saved object needs data attached.
- Recreate the original setup keys and variable order when preparing new data for a saved model.

## Quick Debug Checklist

- `import scvi; scvi.__version__` matches the expected version for the skill or project.
- The selected class is imported from `scvi.model`; the MLX class is `mlxSCVI`, not `MlxSCVI`.
- The exact class's `setup_anndata` was called before construction.
- All `layer`, `batch_key`, `labels_key`, `protein_expression_obsm_key`, and covariate keys exist.
- The input matrix is raw counts or an intentional count layer.
- The model's `train` signature supports the kwargs being passed.
- Optional backends for Pyro or MLX are installed before using those models.
