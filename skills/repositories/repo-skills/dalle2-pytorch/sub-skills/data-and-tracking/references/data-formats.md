# DALLE2-pytorch data formats

DALLE2-pytorch has two main data surfaces: decoder image+embedding WebDatasets and diffusion-prior embedding folders read through `EmbeddingReader`.

## Decoder: `ImageEmbeddingDataset`

Public imports:

```python
from dalle2_pytorch.dataloaders import ImageEmbeddingDataset, create_image_embedding_dataloader
```

Convenience signature surface:

```python
create_image_embedding_dataloader(
    tar_url,
    num_workers,
    batch_size,
    img_embeddings_url=None,
    text_embeddings_url=None,
    index_width=None,
    shuffle_num=None,
    shuffle_shards=True,
    resample_shards=False,
    img_preproc=None,
    extra_keys=[],
    handler=..., 
)
```

### What each WebDataset sample should contain

The decoder dataset returns tuple keys in this order:

1. `jpg`: decoded PIL RGB image, optionally preprocessed.
2. `emb`: dictionary containing `img` and/or `text` embedding tensors.
3. Additional `extra_keys`, for example `txt` captions in the bundled training launcher.

Embeddings can come from either:

- `.npy` entries inside each `.tar` sample; or
- sidecar embedding folders passed through `img_embeddings_url` and/or `text_embeddings_url`.

### Sidecar embedding folder convention

Sidecar `.npy` files must share shard numbers with the WebDataset tar files. The loader finds an example `.npy`, extracts the final underscore-separated shard token, then builds sidecar paths by replacing that shard token.

Example:

```text
shards/0001.tar
img_embeddings/img_emb_0001.npy
text_embeddings/text_emb_0001.npy
```

If a WebDataset sample key ends in index digits, the loader uses the final `index_width` characters to choose the embedding row.

Example:

```text
sample key: 00010509
index_width: 4
embedding row: 509
```

All-zero sidecar embeddings are treated as invalid/missing.

### Sharding fields in decoder configs

- `webdataset_base_url`: pattern with one `{}` slot, for example `data/shards/{}.tar`.
- `start_shard` / `end_shard`: inclusive numeric shard range.
- `shard_width`: zero-padding width for tar names in the training launcher.
- `index_width`: digits at the end of a sample key used as sidecar embedding row index.
- `shuffle_train`: shuffles shard order.
- `resample_train`: samples shards with replacement; cannot be combined with shuffle and needs finite `epoch_samples`.

### Safe checker

```bash
python scripts/validate_webdataset_layout.py \
  --tar-pattern 'data/shards/{}.tar' \
  --start-shard 0 --end-shard 9 \
  --shard-width 4 --index-width 4 \
  --image-embeddings data/img_embeddings \
  --text-embeddings data/text_embeddings
```

By default the checker validates expected tar names and sidecar `.npy` shard files. Add `--inspect-tar` only for a tiny safe shard to inspect member suffixes and sample keys.

## Prior: `PriorEmbeddingDataset`

Public imports:

```python
from dalle2_pytorch.dataloaders import get_reader, make_splits, PriorEmbeddingDataset
```

### Text-conditioned prior

When `condition_on_text_encodings=True`, the prior loader expects image embeddings and caption metadata:

```python
reader = get_reader(text_conditioned=True, img_url="data/img_emb", meta_url="data/meta")
train, val, test = make_splits(
    text_conditioned=True,
    batch_size=128,
    num_data_points=100000,
    train_split=0.8,
    eval_split=0.1,
    image_reader=reader,
)
```

The loader reads image embeddings through `EmbeddingReader` and tokenizes `caption` metadata with `clip.tokenize(..., truncate=True)`.

### Embedding-only prior

When not text-conditioned, `get_reader` requires both image and text embedding folders:

```python
image_reader, text_reader = get_reader(text_conditioned=False, img_url="data/img_emb", txt_url="data/text_emb")
train, val, test = make_splits(
    text_conditioned=False,
    batch_size=128,
    num_data_points=100000,
    train_split=0.8,
    eval_split=0.1,
    image_reader=image_reader,
    text_reader=text_reader,
)
```

### `make_splits` rules

- `start < image_reader.count`.
- `train_split + eval_split < 1.0`; the test split is inferred.
- If `num_data_points` exceeds available reader count, the code prints a warning and uses the reader count.
- `rank` and `world_size` split ranges across distributed processes.
- Each rank must receive at least one sample in each split.

## Image-only dataloader

The package also includes `dalle2_pytorch.dataloaders.simple_image_only_dataloader.get_images_dataloader(folder, batch_size, image_size, ...)` for basic image folders. It is useful for optional VQGAN/VAE-style image training, not the main decoder WebDataset launcher.

## Backend and dependency notes

- S3 WebDataset tar URLs using `s3:` or `pipe:s3cmd ...` require the `s3cmd` executable.
- S3 sidecar embedding URLs require Python package `s3fs` for fsspec access.
- WebDataset, fsspec, numpy, torch, torchvision, PIL, and embedding-reader are installed by the package base dependencies.
- Remote URLs and cloud stores may require credentials; do not assume they are safe to probe without user approval.
