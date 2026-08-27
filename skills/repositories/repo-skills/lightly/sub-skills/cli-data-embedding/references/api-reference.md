# Practical API reference: `lightly.core`, `lightly.embedding`, and embedding I/O

Use this reference when a task should call LightlySSL from Python instead of shelling out to the CLI. For custom training loops and low-level component assembly, route to `training-workflows` or `ssl-building-blocks`.

## `lightly.core` one-liners

`lightly.core` wraps the same train/embed machinery used by the CLI. These functions can train models, load/download pretrained checkpoints, write checkpoints, and compute embeddings, so treat them as runtime operations rather than pure metadata calls.

### `lightly.train_embedding_model(config_path=None, **kwargs)`

Purpose: train a self-supervised embedding model using the CLI default config plus nested keyword overrides.

Returns: path to the trained checkpoint.

Example:

```python
import lightly

checkpoint_path = lightly.train_embedding_model(
    input_dir="data",
    trainer={"max_epochs": 1, "gpus": 0},
    loader={"batch_size": 16, "num_workers": 0},
    collate={"input_size": 64},
    pre_trained=False,
)
```

Notes:

- `config_path` can point to a complete compatible config YAML; otherwise the bundled default is used.
- Nested config namespaces are passed as dictionaries: `trainer={"max_epochs": 1}`, not `trainer.max_epochs=1`.
- Returned checkpoint paths should be captured directly rather than relying on environment variables.

### `lightly.embed_images(checkpoint, config_path=None, **kwargs)`

Purpose: embed images with a checkpoint using the CLI embedding path.

Returns: `(embeddings, labels, filenames)` where embeddings are a NumPy array, labels are integers, and filenames are dataset-relative strings.

Example:

```python
import lightly

embeddings, labels, filenames = lightly.embed_images(
    checkpoint="last.ckpt",
    input_dir="data",
    loader={"batch_size": 64, "num_workers": 0},
    collate={"input_size": 224},
)
```

Notes:

- A checkpoint argument is required by the public function signature.
- For a shell-only workflow, the closest command is `lightly-embed input_dir=data checkpoint=last.ckpt collate.input_size=224`.
- The Python return value is usually easier to consume than a CLI-created `embeddings.csv` when the downstream code is already in Python.

### `lightly.train_model_and_embed_images(config_path=None, **kwargs)`

Purpose: train a model, then embed images with the newly trained checkpoint.

Returns: `(embeddings, labels, filenames)`.

Example:

```python
import lightly

embeddings, labels, filenames = lightly.train_model_and_embed_images(
    input_dir="data",
    trainer={"max_epochs": 1, "gpus": 0},
    loader={"batch_size": 16, "num_workers": 0},
    collate={"input_size": 64},
    pre_trained=False,
)
```

Notes:

- This is the Python analogue of `lightly-magic`.
- It first calls the training path, then passes the resulting checkpoint to the embedding path.
- It can be expensive on real datasets; use bounded epoch/batch/worker settings for smoke runs.

## `lightly.embedding` classes

### `SelfSupervisedEmbedding(model, criterion, optimizer, dataloader, scheduler=None)`

Purpose: a PyTorch Lightning module that trains a self-supervised embedding model and exposes an `embed` method.

Constructor inputs:

- `model`: a Lightly benchmarking-style module/backbone wrapper whose `forward` supports the self-supervised pair used in training and whose `backbone` can produce embeddings.
- `criterion`: self-supervised loss module.
- `optimizer`: PyTorch optimizer.
- `dataloader`: dataloader over a `LightlyDataset` or compatible dataset that returns `(views, label, filename)` for training.
- `scheduler`: optional PyTorch LR scheduler.

Training call shape:

```python
from omegaconf import OmegaConf

trainer_cfg = OmegaConf.create({"max_epochs": 1, "gpus": 0})
checkpoint_cfg = OmegaConf.create({"save_last": True, "save_top_k": 1, "dirpath": "checkpoints"})
summary_cfg = OmegaConf.create({"max_depth": 1})

trainer = encoder.train_embedding(
    trainer_config=trainer_cfg,
    checkpoint_callback_config=checkpoint_cfg,
    summary_callback_config=summary_cfg,
)
checkpoint_path = encoder.checkpoint
```

Embedding call shape:

```python
embeddings, labels, filenames = encoder.embed(dataloader, device=None)
```

Return contract:

- `embeddings`: NumPy array shaped `(n_samples, embedding_feature_size)`.
- `labels`: list of integer labels.
- `filenames`: dataset filenames, sorted in the dataset's filename order.

Important caveats:

- `embed` switches the model to eval mode and calls `self.model.backbone(image_batch)`.
- The dataloader used for embedding should yield image tensors, labels, and filenames.
- The dataset should provide `get_filenames()` for stable output ordering; `LightlyDataset` does.
- `BaseEmbedding.embed` is abstract; use `SelfSupervisedEmbedding` unless implementing a new embedding strategy.

## Embedding CSV utilities

Lightly-compatible embedding CSVs can be handled with `lightly.utils.io`.

### Save embeddings

```python
import numpy as np
from lightly.utils.io import save_embeddings

embeddings = np.array([[0.1, 0.2], [0.3, 0.4]], dtype=float)
labels = [0, 1]
filenames = ["img_0.jpg", "img_1.jpg"]
save_embeddings("embeddings.csv", embeddings, labels, filenames)
```

`save_embeddings` raises `ValueError` if `embeddings`, `labels`, and `filenames` have different lengths.

### Load or validate embeddings

```python
from lightly.utils.io import check_embeddings, load_embeddings, load_embeddings_as_dict

check_embeddings("embeddings.csv")
embeddings, labels, filenames = load_embeddings("embeddings.csv")
embedding_payload = load_embeddings_as_dict("embeddings.csv", embedding_name="default")
```

Validation checks include header spelling, required `labels`, `embedding_*` columns, and absence of empty rows.

## Choosing CLI vs Python API

Prefer CLI when:

- The task is a one-off train/embed/crop operation over folders.
- The user wants reproducible shell commands.
- Hydra output directories and default config behavior are acceptable.

Prefer `lightly.core` when:

- The downstream code is already Python and should receive embeddings directly.
- The caller wants to capture checkpoint/embedding return values instead of parsing CLI output.
- Overrides are naturally nested dictionaries.

Prefer `lightly.embedding` when:

- The task already has custom model/criterion/optimizer/dataloader objects.
- The user needs direct control over the Lightning module and trainer configs.

Route away from this sub-skill for designing a new SSL model architecture or debugging low-level head/loss/transform tensor shapes.
