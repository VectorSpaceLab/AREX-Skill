# Dataloaders Reference

This reference covers `DataSplitter`, `AnnDataLoader`, custom datamodules, and inference loaders used by scvi-tools training and model methods.

## Default Data Path

For ordinary AnnData/MuData workflows, call model setup, construct the model, and let `model.train()` create a `DataSplitter`:

```python
scvi.model.SCVI.setup_anndata(adata, layer="counts", batch_key="batch")
model = scvi.model.SCVI(adata)
model.train(max_epochs=20, batch_size=128, train_size=0.9, validation_size=0.1)
```

Internally, standard models build:

- `scvi.dataloaders.DataSplitter(adata_manager, train_size, validation_size, batch_size, shuffle_set_split, load_sparse_tensor, **datasplitter_kwargs)`.
- `scvi.dataloaders.AnnDataLoader(adata_manager, indices, batch_size=128, shuffle=False, drop_last=False, data_and_attributes=None, distributed_sampler=False, load_sparse_tensor=False, **kwargs)`.

Use direct `DataSplitter`/`AnnDataLoader` construction mainly for debugging, tests, or custom training code.

## `DataSplitter` Knobs

`DataSplitter` creates training, validation, and test dataloaders.

Key arguments:

- `train_size`: float in `(0, 1]`; default behavior is practically `0.9`.
- `validation_size`: float in `[0, 1)` or `None`; if the split sum is below 1, remaining cells are test cells.
- `shuffle_set_split`: controls whether split indices are shuffled before partitioning.
- `load_sparse_tensor`: loads CSR/CSC matrices as sparse `torch.Tensor` objects where supported.
- `pin_memory`: forwards pinned-memory behavior to `AnnDataLoader`.
- `external_indexing`: explicit `[train_idx, val_idx, test_idx]` NumPy arrays.
- Extra kwargs such as `drop_last`, `num_workers`, and `persistent_workers` are forwarded to loaders.

Example with exact external splits:

```python
import numpy as np

train_idx = np.asarray([...])
val_idx = np.asarray([...])
test_idx = np.asarray([], dtype=int)

model.train(
    max_epochs=50,
    batch_size=256,
    datasplitter_kwargs={"external_indexing": [train_idx, val_idx, test_idx]},
)
```

Validation checks reject invalid split sizes, overlapping split indices, non-array external indices, and early-stopping validation monitors without validation cells.

## `AnnDataLoader` Knobs

`AnnDataLoader` returns minibatches from the registered fields in an `AnnDataManager`.

Useful parameters:

- `indices`: observation indices or boolean mask; `None` means all observations.
- `batch_size`: minibatch size per iteration; under distributed sampling, effective global batch size is per-replica batch size multiplied by replica count.
- `shuffle`: uses random sampling when no explicit sampler is supplied.
- `sampler`: custom sampler; cannot be combined with `distributed_sampler=True`.
- `drop_last`: drops incomplete tail batches.
- `data_and_attributes`: subset registry tensors or force loading dtypes.
- `iter_ndarray`: returns NumPy arrays instead of Torch tensors.
- `distributed_sampler`: uses `BatchDistributedSampler` for DDP-compatible batches.
- `load_sparse_tensor`: preserves sparse CSR/CSC layout as sparse Torch tensors where supported.

Direct inspection example:

```python
from scvi.dataloaders import AnnDataLoader

loader = AnnDataLoader(model.adata_manager, batch_size=64, shuffle=False)
batch = next(iter(loader))
print(batch.keys())
```

Batch keys are registry keys such as `X`, `batch`, `labels`, and covariate keys. The exact keys depend on the model setup call.

## Sparse Tensor Loading

For sparse count matrices, especially CSR/CSC inputs moved to GPU, try:

```python
model.train(
    max_epochs=20,
    accelerator="auto",
    devices="auto",
    batch_size=256,
    load_sparse_tensor=True,
)
```

Only use this for sparse matrices and validate model compatibility. If a custom datamodule is supplied, `load_sparse_tensor` from `model.train()` is not applied to that datamodule unless the datamodule implements its own equivalent behavior.

## Custom Datamodules

Custom datamodule support is experimental and backend-specific. Optional extras may be required; a default scvi-tools install may not include LaminDB, TileDB, annbatch, or other custom dataloader dependencies.

Common pattern:

```python
from scvi.dataloaders import MappedCollectionDataModule

# Backend-specific collection creation is omitted here.
datamodule = MappedCollectionDataModule(
    collection,
    batch_key="batch",
    batch_size=1024,
    shuffle=True,
)

model = scvi.model.SCVI(registry=datamodule.registry)
model.train(max_epochs=1, batch_size=1024, datamodule=datamodule)
```

A supported datamodule should provide the properties needed to build or validate the model, such as `registry`, `n_obs`, `n_vars`, `n_batch`, and optionally `n_labels`, `n_continuous_cov`, or `n_cats_per_cov`. If it implements `set_batch_size` or `set_split`, scvi-tools forwards `batch_size`, `train_size`, `validation_size`, and `shuffle_set_split` from `model.train()`.

## Inference Dataloaders

When training or querying with a custom datamodule, use the same datamodule family for inference:

```python
inference_dl = datamodule.inference_dataloader(batch_size=512)

latent = model.get_latent_representation(dataloader=inference_dl)
elbo = model.get_elbo(dataloader=inference_dl)
recon = model.get_reconstruction_error(dataloader=inference_dl)
```

For query or alternate datasets, use an inference dataloader whose registry, gene order, batch labels, label keys, and covariate encodings match the model or query model. Mismatches usually surface as missing keys, shape errors, label encoding errors, or invalid categorical index errors.
