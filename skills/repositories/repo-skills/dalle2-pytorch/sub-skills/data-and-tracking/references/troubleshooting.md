# Data and tracking troubleshooting

## WebDataset sample is missing keys

Symptom:

```text
Sample <key> missing jpg or emb
```

Cause: decoder data pipeline verifies required keys after decoding and embedding insertion.

Fix:

- Ensure each tar sample has a `.jpg` image entry.
- Ensure image embeddings are either inside the tar as `.npy` entries or available through `img_embeddings_url`.
- If text conditioning is enabled and no CLIP adapter is used, ensure text embeddings are present through `text_embeddings_url`.
- Run `scripts/validate_webdataset_layout.py --inspect-tar` on one tiny shard to inspect member suffixes.

## Sidecar embedding row is missing or zero

Symptom:

```text
Webdataset had a sample, but no embedding was found
```

Cause: sidecar `.npy` row selected by the sample key's final `index_width` digits is all zeros or out of alignment.

Fix:

1. Confirm `index_width` matches sample keys.
2. Confirm sidecar `.npy` file shard matches tar shard.
3. Re-run embedding reordering so missing image indices have intentional zero rows only when the image is absent.
4. Use the validation helper to compare expected shard filenames.

## `Cannot both resample and shuffle`

Cause: `ImageEmbeddingDataset` asserts `not shuffle_shards` when `resample=True`.

Fix: set `shuffle_train: false` when `resample_train: true`; set `train.epoch_samples` in the training config.

## S3 or cloud data fails

Symptoms:

- `s3cmd is required for s3 webdataset`.
- `s3fs is required to load embeddings from s3`.
- fsspec authentication or permission errors.

Fix:

- For `pipe:s3cmd get s3://...`, install and configure the `s3cmd` executable.
- For sidecar `s3://...` embedding folders, install Python package `s3fs`.
- Confirm credentials and bucket permissions outside the reusable skill content.
- Prefer local copies for first validation.

## Prior `get_reader` assertion fails

Symptoms:

- `Must supply a image url`.
- `Must supply meta url if text-conditioned`.
- `Must supply text embedding url if not text-conditioning`.

Fix:

- If `condition_on_text_encodings=True`, provide image embeddings plus metadata folder with a `caption` column.
- If not text-conditioned, provide both image and text embedding folders.
- Confirm the `EmbeddingReader` file format expected by the source: text-conditioned image reader uses `parquet_npy` plus `metadata_folder`; non-conditioned readers use `npy`.

## Distributed split has zero samples

Symptom: assertion says calculated rank start/stop length is zero.

Cause: `make_splits` divides data across `world_size`; one split has too few samples for all ranks.

Fix: reduce process count, increase `num_data_points`, or adjust split proportions.

## Tracker path or local checkpoint missing

Symptom: `Model not found at <path>` from local loader.

Cause: `LocalLoader` requires the file unless `only_auto_resume` is true.

Fix: check the path, disable the loader for fresh training, or configure `only_auto_resume` only for auto-resume workflows.

## W&B/HuggingFace errors

Causes:

- Missing `wandb_entity`, `wandb_project`, or `wandb_run_id` for resume.
- Missing HuggingFace login or token file.
- Network or permission problems.

Fix: switch to console/local for dry runs, then re-enable provider savers only after credentials and destination repos are confirmed.

## Data paths in public answers

Do not leak private local data paths or credentials in reusable instructions. Use placeholders like `DATA_ROOT/shards/{}.tar`, `EMBEDDINGS_ROOT/img_emb`, and `TRACKER_ROOT` unless the user explicitly wants a concrete path in their local workspace.
