# Model reference

## CTGAN

Import:

```python
from sdgx.models.ml.single_table.ctgan import CTGANSynthesizerModel
```

Inspected constructor signature:

```python
CTGANSynthesizerModel(
    embedding_dim=128,
    generator_dim=(256, 256),
    discriminator_dim=(256, 256),
    generator_lr=0.0002,
    generator_decay=1e-06,
    discriminator_lr=0.0002,
    discriminator_decay=1e-06,
    batch_size=500,
    discriminator_steps=1,
    log_frequency=True,
    epochs=300,
    pac=10,
    device="cuda" if torch.cuda.is_available() else "cpu",
)
```

Operational notes:

- `batch_size` must be even.
- `fit(metadata, dataloader, epochs=None, ...)` updates `_epochs` when `epochs` is passed.
- CTGAN uses SDGX metadata `discrete_columns` plus its optimized data transformer and `NDArrayLoader` cache.
- `save(save_dir)` and `load(save_dir)` persist `ctgan.pkl` under the model directory.
- Use `device="cpu"` for portable tests; use CUDA only after verifying the active PyTorch environment.

## GaussianCopula

Import:

```python
from sdgx.models.statistics.single_table.copula import GaussianCopulaSynthesizerModel
```

Inspected constructor signature:

```python
GaussianCopulaSynthesizerModel(
    metadata=None,
    enforce_min_max_values=True,
    enforce_rounding=True,
    locales=None,
    numerical_distributions=None,
    default_distribution=None,
)
```

Operational notes:

- `fit(metadata, dataloader, ...)` loads the full processed data into a DataFrame, transforms discrete columns, fits Gaussian copula univariates, and records row count.
- `sample(num_rows, conditions=None)` returns a DataFrame with inverse-transformed columns.
- Distribution names include `norm`, `beta`, `truncnorm`, `uniform`, `gamma`, and `gaussian_kde`; non-parametric distributions can block parameter extraction.
- This model is not listed by `ModelManager().registed_models` in the inspected checkout, so prefer direct import.

## ModelManager facts

```python
from sdgx.models.manager import ModelManager
manager = ModelManager()
print(manager.registed_models.keys())  # observed: dict_keys(['ctgan'])
model = manager.init_model("CTGAN", epochs=1, device="cpu")
```

Manager names are normalized to lowercase, so `"CTGAN"`, `"ctgan"`, and whitespace-trimmed equivalents resolve the same when registered.
