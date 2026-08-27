# Data Input Formats

## Purpose

Read this when choosing `--input_format`, mapping URL/caption/hash/additional columns, using a folder of input files, or predicting shard boundaries before an `img2dataset` run.

## Supported input formats

The supported input formats are exactly:

| `--input_format` | Input shape | Compression | Notes |
| --- | --- | --- | --- |
| `txt` | Plain text, one URL per line | none | Ignores `--url_col` and cannot carry captions, hashes, bbox, or additional columns. |
| `txt.gz` | Gzip text, one URL per line | gzip | Same schema as `txt`. |
| `csv` | Delimited table with headers | none | Use `--url_col`, optional `--caption_col`, optional hash column, and optional `--save_additional_columns`. |
| `csv.gz` | CSV with headers | gzip | Same mapping as `csv`. |
| `tsv` | Tab-delimited table with headers | none | Same mapping as `csv`, with tab delimiter. |
| `tsv.gz` | TSV with headers | gzip | Same mapping as `tsv`. |
| `json` | JSON table readable as a DataFrame | none | Use the same logical column mapping as CSV-like inputs. |
| `json.gz` | JSON table | gzip | Same mapping as `json`. |
| `jsonl` | JSON Lines records | none | One record per line; use the same logical column mapping as CSV-like inputs. |
| `jsonl.gz` | JSON Lines records | gzip | Same mapping as `jsonl`. |
| `parquet` | Parquet table | parquet internal compression | Uses projected column reads for the mapped URL, caption, hash, and additional columns. |

If a different format string is passed, the reader raises an invalid input format error before downloading.

## Column mapping rules

`img2dataset` normalizes selected input columns to internal names before sharding:

| Flag/API parameter | Applies to | Internal name in shard/metadata | Required? | Notes |
| --- | --- | --- | --- | --- |
| `url_list` | file or folder | n/a | yes | Required input path. May be a folder of files matching `*.{input_format}`. |
| `input_format` | all inputs | n/a | yes | Must be one of the exact supported values above. |
| `url_col` | structured inputs | `url` | yes for structured inputs | Default is `url`. For `txt`/`txt.gz`, each line is treated as a URL and this flag is ignored. |
| `caption_col` | structured inputs | `caption` | optional | If `None`, captions are not saved as text files/tar members. If set, the selected column is renamed to `caption` in metadata. |
| `verify_hash` | structured inputs | hash type: `md5`, `sha256`, or `sha512` | optional | Pass as a two-item list: `["input_hash_column", "hash_type"]`. The hash type must match `compute_hash`. |
| `save_additional_columns` | structured inputs | original additional column names | optional | Extra columns are copied into per-sample metadata sidecars/records. Do not include reserved output columns. |
| `bbox_col` | structured inputs | original bbox column name | optional | Owned by image processing. When set, it is also added to saved metadata columns so the blurrer can read it. |

Important behaviors:

- For `txt` and `txt.gz`, the reader's column list is only `url`; captions, hashes, and additional columns cannot be read from the file.
- For CSV/TSV/JSON/JSONL/Parquet inputs, the URL column is renamed to `url`, the caption column is renamed to `caption`, and the verification hash column is renamed to its hash type (`md5`, `sha256`, or `sha512`).
- Additional columns keep their original names and are saved in output metadata.
- Missing selected columns usually surface as table/Arrow/parquet column errors during sharding. Recheck `--url_col`, `--caption_col`, `--verify_hash`, and `--save_additional_columns` spelling.

## Reserved metadata names

Do not put these names in `--save_additional_columns` because `img2dataset` reserves them for its own output metadata:

```text
key, caption, url, width, height, original_width, original_height,
status, error_message, exif, md5, sha256, sha512
```

If a user-provided table has business metadata with one of these names, rename that column before running or omit it from `--save_additional_columns`. The core argument validator raises a clear error for this collision; this reference explains how to fix the schema.

## Hash verification inputs

Use `verify_hash` when the input file already contains an expected raw-image hash.

```bash
img2dataset --url_list urls.parquet --input_format parquet \
  --url_col image_url \
  --compute_hash md5 \
  --verify_hash '["expected_md5","md5"]' \
  --output_format webdataset --output_folder out
```

Rules:

- The first item is the source input column name containing expected hashes.
- The second item is the hash type, one of `md5`, `sha256`, or `sha512`.
- `compute_hash` must equal the verification hash type. For example, `--compute_hash md5` pairs with `--verify_hash '["expected_md5","md5"]'`.
- The verification hash column is used to decide whether a downloaded image matches. It is not duplicated under its original input-column name in metadata; the computed hash is stored under the hash type.
- A mismatch is recorded as `status=failed_to_download` with `error_message=hash mismatch`; no image artifact is written for that sample, but metadata rows can still record the failure for writers with metadata output.

## Additional columns

`save_additional_columns` preserves user metadata alongside downloader metadata.

```bash
img2dataset --url_list urls.csv --input_format csv \
  --url_col image_url --caption_col alt_text \
  --save_additional_columns '["license","source_id","split"]' \
  --output_format files --output_folder out
```

Expected downstream effects:

- For `files`, each successful image has a per-image `.json` metadata file and the shard sidecar parquet includes these additional columns.
- For `webdataset`, each successful tar sample has a `.json` member and the shard sidecar parquet includes these columns.
- For `parquet`, the shard parquet includes metadata columns plus an image-bytes column named after `encode_format` (default `jpg`).
- For `tfrecord`, successful TF Examples include additional metadata features, and the shard sidecar parquet includes the same metadata columns.
- For `dummy`, no image or metadata writer output is produced; downloader stats JSON may still exist after a full run.

## Folder input behavior

`url_list` may be a folder. The reader lists files using a suffix pattern based on the selected input format:

```text
input_parts/*.{input_format}
```

Examples:

| Input folder contents | `--input_format` | Files considered |
| --- | --- | --- |
| `part-000.csv`, `part-001.csv` | `csv` | both CSV files, sorted by name |
| `part-000.jsonl.gz`, `part-001.jsonl.gz` | `jsonl.gz` | both gzipped JSONL files, sorted by name |
| `urls.txt`, `urls.csv` | `txt` | only `*.txt` files |
| `urls.txt.gz` | `txt.gz` | only `*.txt.gz` files |

If no files match, the reader raises a `No file found ... with extension ...` error. Check the folder path, extension, and `--input_format` spelling.

## Sharding behavior

- `number_sample_per_shard` controls how many input rows are placed into each shard before downloading. Default: `10000`.
- The last shard for a file may contain fewer rows.
- For folder inputs, files are processed in sorted order and shard ids continue across files. If the first file makes shard `00000`, the second file begins at the next shard id.
- Done shards are skipped when their shard id is present in the set supplied to the reader. In a normal incremental run, done shards are inferred from root-level `*_stats.json` files written for completed shards.
- Use the same input rows, `number_sample_per_shard`, and output folder when resuming a run. Incremental-mode policy itself is owned by the core download sub-skill.

## Command fragments

```bash
# Plain URL list, no captions.
img2dataset --url_list urls.txt --input_format txt --output_format files --output_folder out

# CSV with non-default names and captions.
img2dataset --url_list urls.csv --input_format csv \
  --url_col image_url --caption_col alt_text \
  --output_format webdataset --output_folder out

# Gzipped JSONL folder, extra metadata, two shards per 20k rows with default shard size.
img2dataset --url_list input_parts --input_format jsonl.gz \
  --save_additional_columns '["license","source_id"]' \
  --number_sample_per_shard 10000 \
  --output_format webdataset --output_folder out

# Parquet input with projected columns and hash verification.
img2dataset --url_list urls.parquet --input_format parquet \
  --url_col image_url --caption_col caption \
  --compute_hash sha256 --verify_hash '["sha256_expected","sha256"]' \
  --save_additional_columns '["dataset","split"]' \
  --output_format parquet --output_folder out
```
