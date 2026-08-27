# Input/Output Format Troubleshooting

## Purpose

Use this when `img2dataset` cannot read an input table, writes a layout different from what the user expected, or an audit finds missing images, captions, metadata columns, sidecars, stats, or TFRecord support.

## Quick triage

1. Confirm the exact `--input_format` and `--output_format` strings against [data formats](data-formats.md) and [output formats](output-formats.md).
2. Check that the input file extension matches the selected format, especially for folder inputs.
3. Verify `--url_col`, `--caption_col`, `--verify_hash`, and `--save_additional_columns` against the actual table schema.
4. Audit the output with the bundled helper:

   ```bash
   python ../scripts/inspect_output_layout.py --output-folder out --expected-format webdataset
   ```

5. If output rows have `status=failed_to_download` or `status=failed_to_resize`, route download causes to `../../core-download/` and resize causes to `../../image-processing/`.

## Failure matrix

| Symptom | Likely cause | What to check | Recovery |
| --- | --- | --- | --- |
| `Invalid input format ...` | Typo or unsupported `--input_format` | The allowed values are exactly `txt`, `txt.gz`, `csv`, `csv.gz`, `tsv`, `tsv.gz`, `json`, `json.gz`, `jsonl`, `jsonl.gz`, `parquet`. | Change the flag to an allowed value or convert the input file first. |
| `No file found ... with extension ...` for a folder input | `url_list` points to a folder, but no child files match `*.{input_format}` | Folder contents and suffixes. `txt.gz` expects `*.txt.gz`; `jsonl.gz` expects `*.jsonl.gz`. | Rename files, choose the matching `--input_format`, or pass a specific file instead of a folder. |
| Missing URL/caption/hash column error from Arrow/Pandas/Parquet | `--url_col`, `--caption_col`, or the first `--verify_hash` item does not match the input schema | Print or inspect table columns before running. For Parquet, projected reads fail if a selected column is absent. | Correct the column flag, normalize headers, or omit optional flags that are not present. |
| Captions are not saved as `.txt` files or tar members | `caption_col` was omitted, input was `txt`/`txt.gz`, or the selected caption column was wrong | The writer only saves text artifacts when `caption_col` is not `None`. Text inputs have no caption column. | Use a structured input with `--caption_col`, then re-run. Audit with `--require-captions`. |
| Captions exist in metadata but not as files | Output format is `parquet` or `tfrecord`, or a writer only exposes captions in metadata/TF features | Check the selected output format. | For per-sample `.txt` artifacts use `files` or `webdataset`; otherwise audit `caption` metadata columns. |
| `You cannot use in save_additional_columns ...` | A requested additional column collides with reserved output metadata names | Reserved names include `key`, `caption`, `url`, geometry/status/error columns, `exif`, and hash names. | Rename the user metadata column before running or omit it. Core command validation owns the error; this sub-skill owns the schema fix. |
| Additional metadata columns missing from output sidecars | `save_additional_columns` omitted, misspelled, not present in the input, or `dummy` output was used | Check the input schema and output format. `dummy` writes no metadata writer output. | Re-run with the correct list and a non-dummy writer. |
| Hash verification always fails with `hash mismatch` | Expected hash column is not the raw downloaded image hash, hash type is wrong, or `compute_hash` does not match `verify_hash` | The second `verify_hash` item must be `md5`, `sha256`, or `sha512` and must equal `compute_hash`. | Recompute expected hashes for raw image bytes or align `--compute_hash` and `--verify_hash`. |
| Expected `files` output but no subfolders/images | `--output_format dummy`, all samples failed, or output folder is incomplete | Run the helper with `--expected-format files`; inspect sidecar parquet `status` and stats JSON. | If the format is wrong, re-run with `--output_format files`; if failures dominate, route to core download or image processing. |
| Expected `webdataset` output but no `.tar` files | Wrong output format, all samples failed before write, or path/listing issue | Root output folder for `*.tar`; stats and sidecar parquet for status. | Re-run with `--output_format webdataset` or fix download/resize failures. |
| Expected `parquet` output but no image-bytes column | Output is a sidecar from `files`, `webdataset`, or `tfrecord`, not primary parquet output | Image bytes column is named after `encode_format`, usually `jpg`, `png`, or `webp`. | Re-run with `--output_format parquet` when image bytes must be in parquet. |
| Expected `tfrecord` but writer fails before writing | Missing optional dependencies | Error text says TFRecords require `tensorflow` and `tensorflow_io`. | Install both packages in the runtime environment, then retry. If using remote paths, verify the TF writer supports the target filesystem. |
| `dummy` output is unexpectedly empty | This is the intended behavior of `--output_format dummy` | Dummy writes no images, tar, parquet, or TFRecord sample output. Full runs may only leave stats JSON. | Use `dummy` only for benchmarks. Re-run with `files`, `webdataset`, `parquet`, or `tfrecord` for real output. |
| Metadata sidecar rows do not match image count | Failed downloads/resizes produce metadata rows without image artifacts; tars/files only contain successful samples | Compare sidecar `status` counts with image/tar-member counts. | Inspect `error_message` and route failures to core download or image processing. Do not assume every input row produced an image. |
| Stats JSON missing for a shard | Run interrupted before downloader wrote stats, or files were manually moved | Look for `00000_stats.json` beside shard outputs. | Treat incremental done-shard detection as unreliable until the shard is rerun or stats are restored. |
| Filesystem prefix works for one writer but not another | Writers do not all use the same path layer; TFRecord has narrower filesystem support | Path prefix such as object storage, HDFS, or custom fsspec backend; selected output format. | Prefer `webdataset`, `files`, or `parquet` for broad fsspec support. For TFRecord, use a verified supported filesystem or local staging. |

## Auditing missing images, captions, and metadata

Run the helper with the expected writer:

```bash
python ../scripts/inspect_output_layout.py \
  --output-folder out \
  --expected-format files \
  --require-captions \
  --sample-limit 3
```

Interpretation tips:

- Image counts smaller than sidecar row counts usually mean some samples failed. Check `status` and `error_message` columns.
- Missing `.txt` files or tar `.txt` members with `--require-captions` means captions were not written for successful samples. Recheck `caption_col` and input format.
- Missing `caption` or additional columns in parquet metadata means the input schema/flags did not select them.
- For `tfrecord`, use the sidecar parquet first; parsing TFRecords requires TensorFlow and is only necessary for feature-level audits.

## Safe schema preflight ideas

Before a large run, inspect only the input headers:

```python
# CSV/TSV/JSONL examples use pandas only for quick schema inspection.
import pandas as pd
print(pd.read_csv("urls.csv", nrows=5).columns.tolist())
print(pd.read_parquet("urls.parquet").columns.tolist())
```

Then build the command from [data formats](data-formats.md). Avoid discovering spelling mistakes after a distributed or large download has already started.
