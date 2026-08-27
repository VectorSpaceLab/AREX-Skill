# Beam And Performance Troubleshooting

Use this guide before re-running expensive TFDS Beam builds or changing storage
layout. Prefer non-launching validation and tiny local smokes first.

## Quick triage checklist

1. Is the exact dataset/config/version specified?
2. Is this a local smoke, full local build, Dataflow/Flink/Spark job, or
   separate Beam pipeline reading prepared TFDS data?
3. Are optional packages installed where they run: local process, Beam workers,
   or both?
4. Is `data_dir` local or `gs://...`, and does the process/worker identity have
   read/write permission?
5. Are overwrite/reuse, checksum registration, shard sizing, file format, and
   deterministic-order policy explicit?
6. Can `scripts/beam_options_helper.py` validate the options string without
   launching Beam?
7. Can the issue be reproduced with `--max_examples_per_split=1` or a dummy
   builder before a full run?

## Symptom table

| Symptom | Likely cause | Action |
|---|---|---|
| `ModuleNotFoundError: apache_beam` | Beam is optional for reading prepared data but required for Beam generation or `tfds.beam.ReadFromTFDS`. | Install an Apache Beam version compatible with the runner and Python environment. For cloud workers, include it through requirements/setup as well. |
| `tfds build DATASET` starts many configs | Dataset has multiple builder configs and none was selected. | Stop if unintended; rerun with `DATASET/CONFIG`, `--config`, or a config index. |
| Local build is slow or runs out of RAM/disk | Direct runner or local generation is being used for a large dataset. | Use `--max_examples_per_split` for smokes; move full generation to a distributed runner and shared storage. |
| Dataflow job fails before workers start | Missing/invalid `project`, `staging_location`, `temp_location`, region, bucket permission, or credentials. | Validate pipeline options, GCS paths, billing/project setup, and worker identity. Do not retry blindly. |
| Workers cannot import the dataset builder | Requirements file/setup package does not install TFDS, a local custom dataset module, or dataset-specific extras. | Add worker dependencies; for custom local builders, use a supported Beam packaging method rather than relying on local checkout imports. |
| GCS path permission error | The active identity lacks bucket read/write/list permission or credentials are not visible to workers. | Confirm anonymous vs user-account vs service-account mode; grant least-privilege access to the exact bucket/prefix. |
| Prepared dataset is silently reused | TFDS found an existing dataset version and `download_mode`/overwrite did not request regeneration. | Confirm reuse is acceptable, or write to a new data directory/version. Avoid overwriting shared data without approval. |
| `NonMatchingChecksumError` or missing checksum | Downloaded content differs from registered checksum or checksums were not registered for a new builder. | For existing public datasets, suspect upstream change or corrupt cache; clear only the affected download cache. For new builders, register checksums in a controlled authoring workflow. |
| Nondeterministic example order surprises tests | `--nondeterministic_order` or `DownloadConfig(nondeterministic_order=True)` was used. | Rebuild deterministically if order is part of acceptance; otherwise update downstream tests to compare sets/keys rather than order. |
| Duplicate or unstable example counts after Beam | Duplicate keys, non-deterministic generators, failed worker transforms, or incorrect shard finalization. | Verify unique keys, deterministic source listing, worker logs, and split metadata; reproduce with a small local Beam pipeline. |
| `ReadFromTFDS` says no examples found | Dataset was not prepared at the selected `data_dir`/version/config. | Build or point to the prepared dataset before using it as Beam input. |
| `ReadFromTFDS` raises about skip/take with batch size | Sliced split such as `train[:100]` was combined with `batch_size != None`. | Use `batch_size=None` for subsplit reads inside Beam, then batch later in the Beam pipeline if needed. |
| Multi-worker input has empty workers | `num_input_pipelines` exceeds shard count. | Rebuild with more shards or reduce worker count; verify `builder.info.splits[SPLIT].num_shards`. |
| `as_dataset()` fails for `array_record` | ArrayRecord adapter is random-access/data-source oriented and does not implement `.as_dataset()` in this TFDS version. | Use `builder.as_data_source(...)` or prepare/read with a `tf.data`-compatible format. |
| Parquet/Riegeli import failure | Optional file-format dependency missing. | Install the format-specific dependency in the local and worker environments, or use TFRecord. |
| High RAM while reading images | Large decode buffers, caching, prefetch/autotune, or unused features. | Disable auto-cache, reduce `override_buffer_size`, skip unused/expensive decoding, tune prefetch/autotune, and benchmark. |

## Pipeline option validation

The CLI expects a comma-separated string like:

```text
runner=DataflowRunner,project=GCP_PROJECT,staging_location=gs://BUCKET/binaries,temp_location=gs://BUCKET/temp
```

Validate without launch:

```bash
python scripts/beam_options_helper.py \
  --options "runner=DataflowRunner,project=GCP_PROJECT,staging_location=gs://BUCKET/binaries,temp_location=gs://BUCKET/temp" \
  --data-dir gs://BUCKET/tensorflow_datasets
```

Common option issues:

- Leading `--` inside `--beam_pipeline_options` is unnecessary for the TFDS CLI;
  use `runner=DataflowRunner`, not `--runner=DataflowRunner`.
- Empty segments from trailing commas are invalid.
- Values containing commas cannot be represented safely because TFDS splits the
  string on commas.
- Dataflow generally needs at least runner, project, staging location, and temp
  location; many jobs also need region, job name, requirements/setup, and worker
  resource options.
- Flink needs runner plus compatible Flink version/configuration or an otherwise
  valid Beam runner setup.

## Determinism and ordering triage

TFDS default Beam writing uses deterministic ordering by key. Before changing
this:

- Check whether downstream split slicing, tests, or reproducibility compare exact
  example order.
- Confirm example keys are stable and unique.
- If using `nondeterministic_order=True`, record that the prepared dataset's
  order is not guaranteed and avoid order-sensitive assertions.
- For non-Beam generators, setting nondeterministic order does not create a Beam
  speedup and can only disable shuffling behavior; use it sparingly.

## GCS and credential triage

Keep credential handling explicit and minimal:

- Public TFDS-hosted GCS data can be checked with `tfds.is_dataset_on_gcs` and
  read with `try_gcs=True` when available.
- Private GCS paths require an approved identity. Do not print secrets, copy
  credential JSON into skill files, or assume the local identity is available on
  Beam workers.
- For Dataflow, both staging/temp locations and the final TFDS `data_dir` must
  be writable by the worker service account.
- For remote training reads, colocate compute and storage when possible.

## Performance triage sequence

1. Benchmark the current pipeline with `tfds.benchmark` and a real batch size.
2. Identify whether the bottleneck is source listing/download, Beam worker
   transform, file writing, remote storage, record reading, decoding, mapping,
   batching, or device input starvation.
3. For generation bottlenecks: inspect Beam metrics/logs, worker dependency
   import failures, hot transforms, shard count, file format, and remote writes.
4. For reading bottlenecks: tune `shuffle_files`, `ReadConfig`, cache order,
   decode/skipped features, batch/prefetch, and file locality.
5. Change one control at a time and re-benchmark.

## When to escalate

Ask for user approval or route to the appropriate sibling sub-skill when:

- The task requires launching a billable Dataflow/Flink/Spark job.
- The task requires writing to or deleting from a shared bucket.
- The failure is from custom builder authoring, feature encoding, dummy data,
  checksums, or tests -> `dataset-authoring`.
- The failure is generic loading/split syntax rather than Beam/performance ->
  `data-loading`.
- The failure is CLI command construction outside Beam/file-format/sharding ->
  `cli-workflows`.
- The task involves external TFRecord, folder datasets, Croissant, HuggingFace,
  or community catalogs -> `formats-and-community`.
