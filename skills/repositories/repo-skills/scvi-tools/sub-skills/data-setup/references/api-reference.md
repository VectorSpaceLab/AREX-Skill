# Data Setup API Reference

## Setup Method Selection

Use the setup method on the exact model class that will be instantiated. Setup records field registries and summary statistics in an `AnnDataManager`; model construction later reads that registry.

### SCVI

```python
scvi.model.SCVI.setup_anndata(
    adata,
    layer="counts",
    batch_key="batch",
    labels_key="labels",
    size_factor_key=None,
    categorical_covariate_keys=["donor"],
    continuous_covariate_keys=["percent_mito"],
)
model = scvi.model.SCVI(adata)
```

Use `layer=None` when raw counts are in `adata.X`. `size_factor_key` must point to a numeric `obs` column if used.

### SCANVI

```python
scvi.model.SCANVI.setup_anndata(
    adata,
    labels_key="labels",
    unlabeled_category="Unknown",
    layer="counts",
    batch_key="batch",
)
```

`labels_key` and `unlabeled_category` are required. Ensure `unlabeled_category` is present in `adata.obs[labels_key]` for unlabeled cells; if not, either add it or choose the correct category string.

### TOTALVI with AnnData

```python
scvi.model.TOTALVI.setup_anndata(
    adata,
    protein_expression_obsm_key="protein_expression",
    protein_names_uns_key="protein_names",
    batch_key="batch",
    layer="counts",
)
```

`protein_expression_obsm_key` must exist in `adata.obsm` and have one row per cell. If the value is a DataFrame, column names become protein names; otherwise pass `protein_names_uns_key` pointing to `adata.uns` names or accept sequential names.

### TOTALVI with MuData

```python
scvi.model.TOTALVI.setup_mudata(
    mdata,
    rna_layer=None,
    protein_layer=None,
    batch_key="batch",
    modalities={"rna_layer": "rna", "protein_layer": "protein_expression", "batch_key": "rna"},
)
```

`modalities` is required. `rna_layer=None` and `protein_layer=None` mean use `.X` in each mapped modality.

### PEAKVI

```python
scvi.model.PEAKVI.setup_anndata(
    adata,
    batch_key="batch",
    labels_key="labels",
    layer="counts",
)
```

Use raw chromatin accessibility fragment/count matrices. If data are binarized or read counts rather than fragment counts, resolve that upstream before relying on model outputs.

### MULTIVI with MuData

```python
scvi.model.MULTIVI.setup_mudata(
    mdata,
    rna_layer=None,
    atac_layer=None,
    protein_layer=None,
    batch_key="batch",
    modalities={
        "rna_layer": "rna",
        "atac_layer": "accessibility",
        "protein_layer": "protein_expression",
        "batch_key": "rna",
    },
)
```

At least one mapped modality must contain each role needed by the intended `MULTIVI` configuration. `size_factor_key` for `MULTIVI.setup_mudata` is a joint numeric field; if used for RNA and ATAC it should be shaped with RNA in the first column and ATAC in the second, with ATAC factors normalized between 0 and 1.

## Preprocessing APIs

### poisson_gene_selection

```python
hvg = scvi.data.poisson_gene_selection(
    adata,
    layer="counts",
    n_top_genes=4000,
    batch_key="batch",
    subset=False,
    inplace=False,
    accelerator="auto",
    device="auto",
    n_samples=10000,
    minibatch_size=5000,
)
```

This method expects raw non-negative integer counts. With `inplace=True` or `subset=True`, it writes `adata.uns["hvg"]` and `adata.var` columns: `highly_variable`, `observed_fraction_zeros`, `expected_fraction_zeros`, `prob_zero_enriched_nbatches`, `prob_zero_enrichment`, and `prob_zero_enrichment_rank`. With `subset=True`, it subsets variables in place.

### Reader Imports

```python
from scvi.data import read_10x_atac, read_10x_multiome, read_h5ad, read_csv, read_loom, read_text
```

Prefer `read_h5ad` for persisted AnnData, 10x ATAC readers for raw 10x matrix directories, and `read_csv`/`read_text` only when you can verify orientation and metadata afterward.

## AnnDataManager Inspection

After setup and model construction:

```python
manager = model.adata_manager
print(manager.summary_stats)
print(manager.data_registry)
print(manager.registry)
```

Useful methods and properties:

- `manager.validate()` re-registers fields if another manager setup touched the same data object.
- `manager.transfer_fields(adata_target, **kwargs)` creates a new manager for compatible target data using the source registry.
- `manager.get_from_registry("X")` fetches the matrix or field registered under a registry key.
- `manager.create_torch_dataset(indices=None, data_and_attributes=None, load_sparse_tensor=False)` creates an `AnnTorchDataset` for registered tensors.

## Field Behavior to Remember

- `LayerField` records whether data came from `X` or `layers[layer]`, validates count-like values, corrects dense/sparse memory format when configured, and stores `n_obs`, `n_vars`, and column names.
- `CategoricalObsField` and `CategoricalJointObsField` encode categorical `obs` columns for batch, labels, and covariates.
- `NumericalObsField` and `NumericalJointObsField` validate numeric `obs` columns for size factors and continuous covariates.
- `ProteinObsmField` and `MuDataProteinLayerField` can compute a per-batch protein mask when some batches have all-zero proteins.
- MuData wrapper fields apply the same validations inside mapped modalities and can require modalities with `mod_required=True`.
