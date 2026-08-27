# Training and Dataloader Troubleshooting

Use these checks when `model.train(...)`, callbacks, devices, or custom dataloaders fail.

## CPU-Only Machine but User Requested GPU

Symptoms:

- `accelerator="gpu"` raises no CUDA devices found, CUDA initialization, or GPU backend errors.
- `devices=-1` does not find devices.
- GPU extras were not installed or Torch is CPU-only.

Fix:

```python
import torch

if torch.cuda.is_available():
    model.train(max_epochs=20, accelerator="gpu", devices=1)
else:
    model.train(max_epochs=20, accelerator="cpu", devices=1)
```

Explain that `accelerator="auto"` is the safest portable default, but it cannot create GPU support on CPU-only Torch builds or machines without compatible NVIDIA drivers. For multi-GPU DDP, require a CUDA-capable install and run from a script where possible.

## DDP or Multi-GPU Training Fails

Checks:

- Use `accelerator="gpu", devices=-1` only on a CUDA/NVIDIA multi-GPU machine.
- In scripts, use `strategy="ddp_find_unused_parameters_true"`.
- In notebooks, use `strategy="ddp_notebook_find_unused_parameters_true"`, but prefer scripts for repeatability.
- Set `early_stopping=False`; scvi-tools also disables early stopping when distributed sampling is active.
- Avoid relying on validation-heavy callbacks unless each process and dataloader split is configured correctly.

Example:

```python
model.train(
    max_epochs=100,
    accelerator="gpu",
    devices=-1,
    strategy="ddp_find_unused_parameters_true",
    early_stopping=False,
)
```

## Early Stopping Monitor Error

Symptoms:

- Error says early stopping cannot run with a validation monitor and no validation set.
- Monitor key such as `elbo_validation` never appears.

Fix:

- Keep a validation split: `train_size=0.9, validation_size=0.1`.
- Set `check_val_every_n_epoch=1` when monitoring validation metrics.
- Use a supported monitor such as `elbo_validation`, `reconstruction_loss_validation`, or `kl_local_validation` for standard training plans.
- Disable early stopping when validation is intentionally absent.

```python
model.train(
    max_epochs=100,
    train_size=0.9,
    validation_size=0.1,
    early_stopping=True,
    early_stopping_monitor="elbo_validation",
    check_val_every_n_epoch=1,
)
```

## Tiny Last Batch Warning or BatchNorm-Like Failures

Symptoms:

- Warning says the last batch has only one or two samples.
- Training fails on very small final minibatches.

Fix:

- Change `batch_size` so `n_train % batch_size` is not 1 or 2.
- Pass an explicit `train_size` to control the split.
- Use `datasplitter_kwargs={"drop_last": True}` if losing tail training cells is acceptable.

```python
model.train(
    max_epochs=20,
    batch_size=256,
    train_size=0.85,
    datasplitter_kwargs={"drop_last": True},
)
```

## Invalid Explicit Split Indices

Symptoms:

- Duplicate-index warning in train, validation, or test set.
- Error for overlapping train/validation/test indices.
- Error that external indexing is not a list or elements are not NumPy arrays.

Fix:

```python
import numpy as np

train_idx = np.asarray(train_idx, dtype=int)
val_idx = np.asarray(val_idx, dtype=int)
test_idx = np.asarray(test_idx, dtype=int)

assert len(set(train_idx) & set(val_idx)) == 0
assert len(set(train_idx) & set(test_idx)) == 0
assert len(set(val_idx) & set(test_idx)) == 0

model.train(datasplitter_kwargs={"external_indexing": [train_idx, val_idx, test_idx]})
```

## Custom Dataloader Has Mismatched Batch or Label Keys

Symptoms:

- Key errors for `batch`, `labels`, or covariate keys.
- Shape errors during module construction.
- Categorical index or label encoder errors during training/inference.
- Inference methods fail only when `dataloader=...` is supplied.

Fix checklist:

1. Print the datamodule registry and compare it to the model setup expectations.
2. Confirm the datamodule exposes the same `batch_key`, `label_key`, covariate keys, and feature order used to create `registry=datamodule.registry`.
3. Confirm `n_vars`, `n_batch`, `n_labels`, and covariate counts match the model's expected dimensions.
4. For inference, use `datamodule.inference_dataloader(...)` from the same datamodule family, not a raw PyTorch loader with different keys.
5. If a model was built from AnnData, do not pass a custom datamodule unless that model path explicitly supports replacing the default splitter.

Debug snippet:

```python
print(datamodule.registry.keys())
print(getattr(datamodule, "n_vars", None), getattr(datamodule, "n_batch", None))

inference_dl = datamodule.inference_dataloader(batch_size=512)
batch = next(iter(inference_dl))
print(batch.keys() if hasattr(batch, "keys") else type(batch))
```

## `load_sparse_tensor=True` Does Not Help or Fails

Checks:

- The source matrix must be sparse CSR or CSC to preserve sparse layout.
- Use it through default training, not as an expectation that arbitrary custom datamodules will adopt it.
- If a model operation does not support sparse tensors, retry with `load_sparse_tensor=False` and smaller `batch_size`.

```python
model.train(max_epochs=20, batch_size=128, load_sparse_tensor=False)
```

## Callback or Checkpoint Monitor Missing

Symptoms:

- `SaveCheckpoint` or early stopping cannot find a metric.
- No checkpoint appears when expected.

Fix:

- Use a monitor logged by the active training plan, commonly `elbo_validation`.
- Ensure validation is checked by setting `check_val_every_n_epoch=1`.
- Use `enable_checkpointing=True` for default scvi checkpointing, or pass `callbacks=[SaveCheckpoint(...)]` manually.

```python
from scvi.train import SaveCheckpoint

model.train(
    max_epochs=50,
    check_val_every_n_epoch=1,
    callbacks=[SaveCheckpoint(monitor="elbo_validation", load_best_on_end=True)],
)
```
