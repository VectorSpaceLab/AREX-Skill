# Dataset Recipes

## Purpose

Read this when a user asks for a common public dataset recipe, column mapping, or scale note for img2dataset. These are reference patterns, not verification cases.

## Reading this table

- The recipes below summarize the public command shapes from the repository examples and dataset notes.
- They are intentionally concise: use them to pick the right columns, output format, and tuning defaults.
- Large public datasets usually require distributed execution, restartable outputs, and careful storage planning.

## Common recipes

| Dataset | Typical input format | Common URL column | Common caption column | Typical output | Useful extra columns / notes |
| --- | --- | --- | --- | --- | --- |
| MSCOCO | parquet | `URL` | `TEXT` | `webdataset` | Smallish benchmark-style recipe; good for quick smoke-oriented examples. |
| SBU Captions | json | `image_urls` | `captions` | `webdataset` | JSON input from extracted metadata; good column-mapping example. |
| CC3M | parquet | `url` | `caption` | `webdataset` | Classic image-text pairing recipe; often used with W&B logging in examples. |
| CC12M | parquet | `url` | `caption` | `webdataset` | Same basic shape as CC3M, just larger. |
| LAION-400M | parquet | `URL` | `TEXT` | `webdataset` | Often paired with `save_additional_columns` such as `NSFW`, `similarity`, and `LICENSE`. |
| LAION-5B family | parquet | `URL` | `TEXT` | `webdataset` | Huge-scale recipes; distributed execution and restartable outputs are strongly recommended. |
| LAION-aesthetic / art / high-resolution / COCO / face | parquet | `URL` | `TEXT` | `webdataset` | Common extra columns include `similarity`, `hash`, `punsafe`, `pwatermark`, `aesthetic`, or subset-specific fields. |
| COYO-700M | parquet | `url` | `text` | `webdataset` | Often uses `resize_only_if_bigger=True`, `resize_mode=keep_ratio`, and `skip_reencode=True` at larger sizes. |
| CommonPool | parquet | `url` | `text` | `webdataset` | Upstream DataComp-linked recipe; usually follows the upstream dataset download guidance. |
| DataComp-1B | parquet | `url` | `text` | `webdataset` | Derived from CommonPool and usually follows the upstream DataComp instructions. |

## Selection tips

- Use `webdataset` for most large ML use cases.
- Use `parquet` output when the downstream workflow wants columnar filtering or Spark-friendly inspection.
- Use `files` only for smaller local runs or debugging.
- Use `tfrecord` when the downstream ecosystem is TensorFlow-centric and the optional TensorFlow dependencies are installed.
- Use `dummy` for benchmarking command construction or throughput logic without writing images.

## Scale and tuning notes

- Most of these recipes are network-heavy and dataset-scale. Treat them as commands to adapt, not as default verification runs.
- Many of the larger recipes benefit from `processes_count`, `thread_count`, `subjob_size`, restartable output folders, and optional distributed execution.
- `save_additional_columns` should mirror only the fields the downstream workflow needs; avoid copying every upstream column by default.
- `enable_wandb=True` is optional and should be used only when live metrics are desired.

## Where to go next

- Use `core-download` for the command mechanics and recovery behavior.
- Use `input-output-formats` for exact column mapping and writer layouts.
- Use `distributed-execution` for cluster-sized runs and throughput planning.
