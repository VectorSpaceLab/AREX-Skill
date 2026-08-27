---
name: input-output-formats
description: "Choose and validate img2dataset input schemas, output formats,
  writer layouts, metadata sidecars, captions, hashes, additional columns, and
  TFRecord prerequisites."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Input and Output Formats

Use this sub-skill when the task is about choosing, constructing, or auditing `img2dataset` input and output formats.

## Trigger when the user asks about

- Supported `--input_format` values or converting a URL table into an `img2dataset` input.
- Non-default URL, caption, hash, or metadata columns (`--url_col`, `--caption_col`, `--verify_hash`, `--save_additional_columns`).
- Using a folder of input files, shard sizing, skipped/done shards, or expected shard names.
- Choosing `--output_format` among `files`, `webdataset`, `parquet`, `tfrecord`, and `dummy`.
- Expected output layouts: per-image files, tar members, parquet metadata sidecars, stats JSON, captions, image bytes in parquet/TFRecord, and dummy benchmark outputs.
- Auditing an existing output folder for missing images, captions, metadata columns, shard sidecars, or TFRecord prerequisites.

## Route elsewhere

- Core download retries, SSL, X-Robots-Tag behavior, incremental mode policy, and command orchestration belong to `../core-download/`.
- Resize modes, filters, encoding quality/format tradeoffs, re-encoding, and bounding-box blur belong to `../image-processing/`.
- PySpark/Ray, throughput tuning, DNS, filesystem performance, W&B, and cluster execution belong to `../distributed-execution/`.

## Short workflow

1. Read [data-formats](references/data-formats.md) to pick the exact `--input_format`, column mapping flags, folder behavior, hash verification columns, additional metadata columns, and shard sizing.
2. Read [output-formats](references/output-formats.md) to choose the writer and know the exact files/columns to expect after a run.
3. For an existing output, run the bundled layout helper:

   ```bash
   python sub-skills/input-output-formats/scripts/inspect_output_layout.py \
     --output-folder out \
     --expected-format webdataset \
     --require-captions
   ```

4. If the helper reports schema, caption, missing-column, optional-dependency, or filesystem-prefix problems, use [troubleshooting](references/troubleshooting.md) before changing downloader, resize, or distributed settings.

## Safe bundled helper

- [scripts/inspect_output_layout.py](scripts/inspect_output_layout.py) inspects a completed output folder without importing `img2dataset`. It lists shards, subfolders, tars, parquets, TFRecords, stats JSON, tar members, and parquet metadata columns when optional readers are installed. It exits nonzero for clear mismatches such as an expected writer layout not being present, dummy outputs containing image artifacts, or required captions being absent.

## Common command fragments

```bash
# CSV with non-default URL/caption columns and extra metadata saved into output metadata.
img2dataset --url_list urls.csv --input_format csv \
  --url_col image_url --caption_col alt_text \
  --save_additional_columns '["license","source_id"]' \
  --output_format webdataset --output_folder out

# Parquet input with hash verification and parquet output containing image bytes.
img2dataset --url_list urls.parquet --input_format parquet \
  --url_col image_url --caption_col caption \
  --compute_hash md5 --verify_hash '["expected_md5","md5"]' \
  --output_format parquet --output_folder out

# Folder input: every file matching the selected extension is sharded in sorted order.
img2dataset --url_list input_parts --input_format jsonl.gz \
  --number_sample_per_shard 10000 --output_format webdataset --output_folder out
```
