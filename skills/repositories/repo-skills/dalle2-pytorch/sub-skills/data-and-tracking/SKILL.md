---
name: data-and-tracking
description: "Use DALLE2-pytorch dataloaders, WebDataset and embedding layouts,
  tracker/log/save/load configuration, and safe data-layout diagnostics for
  training workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# data-and-tracking

Use this sub-skill when the task is to prepare DALLE2-pytorch training data, validate WebDataset/embedding shard layout, configure `ImageEmbeddingDataset` or `PriorEmbeddingDataset`, or set up experiment trackers, checkpoint loading, and checkpoint saving.

## Load This When

- Checking decoder WebDataset `.tar` shards, `.jpg`/`.npy` keys, sidecar image/text embedding folders, shard widths, or `index_width`.
- Using `create_image_embedding_dataloader`, `ImageEmbeddingDataset`, `get_reader`, `make_splits`, or `PriorEmbeddingDataset`.
- Debugging S3/fsspec data URLs, `s3cmd`, `s3fs`, missing embeddings, zero sidecar embeddings, or resampling/shuffling behavior.
- Configuring console/W&B logging, local/URL/W&B checkpoint loading, or local/W&B/HuggingFace saving.
- Separating public package workflow guidance from credentials, private data, and tracker artifacts.

## Route Elsewhere

- Model architecture, prior/decoder construction, `DALLE2`, `dream`, inpainting, or CLIP adapters: `../generation-and-api/SKILL.md`.
- JSON training configs, trainer APIs, launcher commands, and distributed training: `../training-and-configs/SKILL.md`.

## Runtime Contract

- Public package: `pip install dalle2-pytorch`.
- Public data imports: `from dalle2_pytorch.dataloaders import ImageEmbeddingDataset, create_image_embedding_dataloader, get_reader, make_splits, PriorEmbeddingDataset`.
- Public tracker/config imports: `from dalle2_pytorch.train_configs import TrackerConfig`; tracker provider behavior lives behind config classes.
- This skill does not provide datasets, credentials, model weights, S3 buckets, W&B runs, or HuggingFace tokens. It helps validate user-provided paths/configs safely.

## References And Bundled Script

- Decoder and prior data formats: [references/data-formats.md](references/data-formats.md).
- Tracker, loader, saver, and checkpoint destinations: [references/tracking-and-checkpoints.md](references/tracking-and-checkpoints.md).
- Data/tracker troubleshooting: [references/troubleshooting.md](references/troubleshooting.md).
- Safe layout checker: [scripts/validate_webdataset_layout.py](scripts/validate_webdataset_layout.py).

## Typical Flow

1. Read [references/data-formats.md](references/data-formats.md) to decide whether the task uses decoder WebDataset shards or prior EmbeddingReader folders.
2. For decoder configs, inspect shard and sidecar naming without loading large data:

   ```bash
   python scripts/validate_webdataset_layout.py --tar-pattern 'data/shards/{}.tar' --start-shard 0 --end-shard 9 --shard-width 1 --index-width 4
   ```

3. Add sidecar folders when embeddings are outside the tar files:

   ```bash
   python scripts/validate_webdataset_layout.py --tar-pattern 'data/shards/{}.tar' --start-shard 0 --end-shard 9 --shard-width 1 --index-width 4 --image-embeddings data/img_emb --text-embeddings data/text_emb
   ```

4. Read [references/tracking-and-checkpoints.md](references/tracking-and-checkpoints.md) before enabling W&B, HuggingFace, S3, URL loaders, or auto-resume.

## Safety Defaults

- Prefer local filesystem paths and `log_type: console` for first checks.
- Do not inspect or upload private tracker credentials; require the user to supply and approve them at execution time.
- Treat network, S3, W&B, HuggingFace, and URL loaders/savers as credentialed or networked workflows, not default smoke tests.
- Use `--inspect-tar` on at most a small shard; otherwise the bundled checker only validates names and file existence.
