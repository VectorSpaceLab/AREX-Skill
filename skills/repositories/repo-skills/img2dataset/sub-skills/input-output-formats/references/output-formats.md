# Output Formats and Layouts

## Purpose

Read this when choosing `--output_format` or auditing the files that `img2dataset` should create after a run.

## Supported output formats

The supported output formats are exactly:

```text
files, webdataset, parquet, tfrecord, dummy
```

Passing any other value raises an invalid output format error.

## Decision table

| `--output_format` | Best fit | Tradeoffs and notes |
| --- | --- | --- |
| `files` | Small/local datasets, quick inspection, simple downstream scripts | Saves ordinary image files under shard subfolders. Good up to roughly 1M samples on a local filesystem; many files become slow and hard to manage at scale. |
| `webdataset` | Large ML datasets and most training pipelines | Saves shard tar files using WebDataset conventions. Works well with PyTorch/TensorFlow/JAX loaders and avoids millions of filesystem entries. This is usually the best default for large runs. |
| `parquet` | Columnar filtering, Spark/PyArrow/PySpark data ecosystems | Saves one shard parquet with image bytes and metadata columns. Convenient for filtering and Spark, but often less direct than WebDataset for training. |
| `tfrecord` | TensorFlow-only ecosystems and `tf.data` pipelines | Saves TFRecord shards plus parquet metadata sidecars. Requires `tensorflow` and `tensorflow_io`. The writer does not use the same fsspec path layer as the other writers, so filesystem support is narrower and can be less efficient away from local storage. |
| `dummy` | Benchmarks that should exercise reading/downloading/resizing without writing samples | Does not save images or metadata writer output. Full downloader runs may still create stats JSON. Use only when empty sample output is intentional. |

## Writer class map

| `--output_format` | Writer class | Parquet helper use |
| --- | --- | --- |
| `files` | `FilesSampleWriter` | Uses `BufferedParquetWriter` for the root shard metadata sidecar. |
| `webdataset` | `WebDatasetSampleWriter` | Uses `BufferedParquetWriter` for the root shard metadata sidecar. |
| `parquet` | `ParquetSampleWriter` | Uses `BufferedParquetWriter` for the primary shard parquet containing metadata plus image bytes. |
| `tfrecord` | `TFRecordSampleWriter` | Uses `BufferedParquetWriter` for the root shard metadata sidecar while TFRecord stores image samples. |
| `dummy` | `DummySampleWriter` | Does not use a parquet writer and does not write sample artifacts. |

## Shard names and keys

- Shard files and folders are zero-padded using `oom_shard_count`; the default produces names like `00000`.
- Sample keys combine the zero-padded shard id with the sample index within that shard. With default settings, keys look like `000000000` for shard `00000`, item `0`.
- `number_sample_per_shard` controls how many rows go into one shard; output layouts are one folder/tar/parquet/tfrecord per shard except for `dummy`.

## Common metadata columns

Metadata is written per sample for all non-dummy writers. The usual downloader metadata includes:

```text
url, key, status, error_message, width, height,
original_width, original_height, exif, md5/sha256/sha512
```

Additional columns may include:

- `caption` when `--caption_col` is set on a structured input.
- The columns listed in `--save_additional_columns`.
- A bbox column when bbox blurring is enabled by the image-processing workflow.
- One hash column named after `compute_hash` when `compute_hash` is not `None`.

Exact columns vary with `input_format`, `caption_col`, `extract_exif`, `compute_hash`, and additional columns. For `txt`/`txt.gz` input, there is no input caption column.

## `files` layout

Expected layout after a completed shard:

```text
out/
  00000/
    000000000.jpg
    000000000.json
    000000000.txt        # only when captions are enabled
    000000001.jpg
    000000001.json
  00000.parquet          # shard metadata sidecar
  00000_stats.json       # downloader stats for the shard
```

Facts to preserve:

- Image extension follows `encode_format` (`jpg` by default; image-processing owns encode choices).
- Each successful sample has an image file and a `.json` metadata file under the shard subfolder.
- If `caption_col` is set, successful samples also get `.txt` caption files. Missing captions become empty text files.
- The root-level shard parquet sidecar contains metadata rows, including failure rows for samples that did not write image files.
- The root-level `*_stats.json` records shard-level counts such as successes and failures.

## `webdataset` layout

Expected layout after a completed shard:

```text
out/
  00000.tar
    000000000.jpg
    000000000.json
    000000000.txt        # only when captions are enabled
    000000001.jpg
    000000001.json
  00000.parquet          # shard metadata sidecar
  00000_stats.json       # downloader stats for the shard
```

Facts to preserve:

- The tar writer writes only successful image samples into the tar.
- Each successful tar sample includes image bytes and a JSON metadata member.
- If captions are enabled, each successful tar sample includes a `.txt` member with the caption text.
- The sidecar parquet records metadata for the shard and can be used to audit status counts and metadata columns efficiently.

## `parquet` layout

Expected layout after a completed shard:

```text
out/
  00000.parquet          # metadata columns plus an image-bytes column
  00000_stats.json       # downloader stats for the shard
```

Facts to preserve:

- The shard parquet is the primary sample output, not just a sidecar.
- It contains metadata columns plus an image bytes column named after `encode_format` (`jpg` by default; also possible: `png` or `webp` when configured).
- Captions are represented as metadata, normally the normalized `caption` column from `caption_col`.
- Failed downloads or failed resizes can appear as rows with a null image-bytes value and failure status.

## `tfrecord` layout

Expected layout after a completed shard:

```text
out/
  00000.tfrecord         # serialized TF Examples for successful images
  00000.parquet          # shard metadata sidecar
  00000_stats.json       # downloader stats for the shard
```

Facts to preserve:

- TFRecord output requires both `tensorflow` and `tensorflow_io` importability. If either is missing, the writer raises a message saying TFRecords require those packages and suggests installing them.
- Successful examples include `key`, the image bytes feature named after `encode_format`, optional `txt` when captions are enabled, and metadata features.
- The sidecar parquet is the easiest way to audit metadata columns without parsing TFRecords.
- Because this writer does not use the same fsspec path layer as other writers, prefer local paths or verify support before writing to remote filesystems.

## `dummy` layout

Expected layout after a completed run:

```text
out/
  00000_stats.json       # possible after the full downloader completes
```

Facts to preserve:

- `dummy` deliberately writes no images, no tar shards, no parquet writer output, and no TFRecord shards.
- A direct `DummySampleWriter` use can leave the folder completely empty.
- If the user expected images, `dummy` is the wrong `--output_format`.

## Stats JSON

Root-level `*_stats.json` files are written by the downloader for completed shards. They are also used by incremental runs to determine done shards. Typical keys include:

```text
count, successes, failed_to_download, failed_to_resize,
duration, start_time, end_time, status_dict
```

If an output folder has images/tars/parquets but no stats JSON for a shard, treat the run as incomplete or manually modified before relying on incremental resume behavior.

## Validation snippets

Use the bundled helper from the sub-skill root:

```bash
# Check a WebDataset output and require caption members/columns.
python sub-skills/input-output-formats/scripts/inspect_output_layout.py \
  --output-folder out --expected-format webdataset --require-captions

# Check a parquet output for a likely image-bytes column and metadata columns.
python sub-skills/input-output-formats/scripts/inspect_output_layout.py \
  --output-folder out --expected-format parquet

# Confirm that a benchmark run really produced no sample artifacts.
python sub-skills/input-output-formats/scripts/inspect_output_layout.py \
  --output-folder out --expected-format dummy
```

Minimal Python column inspection if the helper is not available:

```python
import pandas as pd

df = pd.read_parquet("out/00000.parquet")
print(df.columns.tolist())
print(df[["status", "error_message"]].value_counts(dropna=False))
```

For `files`, `webdataset`, and `tfrecord`, use the sidecar parquet for metadata audits. For `parquet`, the same shard parquet contains both metadata and image bytes.

## Caption expectations by writer

| Writer | Caption artifact when `caption_col` is set | Audit path |
| --- | --- | --- |
| `files` | Per-image `.txt` file under the shard subfolder, plus `caption` metadata | Count `.txt` files and inspect sidecar parquet columns. |
| `webdataset` | Per-sample `.txt` tar member, plus `caption` metadata | Count `.txt` members and inspect sidecar parquet columns. |
| `parquet` | `caption` metadata column | Inspect shard parquet columns/rows. |
| `tfrecord` | Optional `txt` TF feature, plus `caption` sidecar metadata | Prefer sidecar parquet for metadata; parse TFRecords only when TensorFlow is available and needed. |
| `dummy` | none | Captions are intentionally not written. |
