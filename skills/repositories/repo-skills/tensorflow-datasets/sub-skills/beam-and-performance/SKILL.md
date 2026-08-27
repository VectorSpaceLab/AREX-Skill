---
name: beam-and-performance
description: "Scale TensorFlow Datasets generation and reading with Beam,
  storage, sharding, GCS, and performance controls."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Beam And Performance

Use this sub-skill when the task is to scale TensorFlow Datasets (TFDS) dataset
preparation or reading with Apache Beam, cloud runners, file formats, sharding,
GCS data directories, or `tf.data` performance controls.

Route other work away:

- Generic `tfds.load`, split syntax, metadata inspection, NumPy/DataFrame, and
  non-Beam loading recipes -> `data-loading`.
- Full `tfds` CLI syntax outside Beam/file-format/sharding flags ->
  `cli-workflows`.
- Creating ordinary `GeneratorBasedBuilder` datasets, `_info`, features,
  checksums, dummy data, and `DatasetBuilderTestCase` -> `dataset-authoring`.
- Folder datasets, external TFRecord layouts, HuggingFace/Croissant/community
  catalogs, and dataset collections -> `formats-and-community`.

## Evidence-backed API surface

The TFDS code and environment verification for this skill established these
runtime facts:

- Beam generation is configured through `tfds.download.DownloadConfig` fields
  including `beam_runner`, `beam_options`, `max_examples_per_split`,
  `num_shards`, `min_shard_size`, `max_shard_size`, and
  `nondeterministic_order`.
- `tfds build --beam_pipeline_options=...` stores a comma-separated options
  string; TFDS turns each `key=value` segment into a Beam `PipelineOptions` flag
  without launching Beam during parsing.
- Supported prepared-file format names are `tfrecord`, `array_record`,
  `riegeli`, and `parquet`; TFRecord is the default. Some formats require extra
  reader/writer dependencies or different reading APIs.
- `tfds.core.BeamBasedBuilder` still exists but is deprecated; current Beam
  authoring should normally use `GeneratorBasedBuilder` whose
  `_generate_examples` returns a Beam `PTransform`/`PCollection`.
- `tfds.beam.ReadFromTFDS` reads an already prepared TFDS dataset inside a Beam
  pipeline, parallelizing over dataset shards.
- Dataflow, Flink, private GCS, and service-account credentials are external
  services; do not run or mutate them without explicit user approval, budget,
  and credential boundaries.

## Fast workflow chooser

| User intent | Use |
|---|---|
| "Build this huge TFDS dataset locally just to test the builder" | Direct/local Beam runner plus a tiny `--max_examples_per_split` or programmatic `DownloadConfig(max_examples_per_split=...)`; warn that full local builds can exceed RAM/disk/time. |
| "Run TFDS generation on Dataflow" | Build a GCS-backed `data_dir`, `staging_location`, `temp_location`, `requirements_file`, and `runner=DataflowRunner`; verify project/bucket/credentials before launch. |
| "Use Flink" | Pass `runner=FlinkRunner` plus Flink version/config-dir options; verify Beam/Flink version compatibility externally. |
| "Use TFDS as source inside Beam" | Use `tfds.beam.ReadFromTFDS(builder, split=...)` only after the dataset is prepared; respect subsplit/batch limitations. |
| "Improve reading throughput/RAM" | Tune `ReadConfig`, shuffling, cache/batch/prefetch order, decode/skipped features, file format, and GCS locality. |
| "Change shard count/size or file format" | Use generation flags or `DownloadConfig`/`download_and_prepare(file_format=...)`; validate reader compatibility before rebuilding. |

## Standard playbooks

1. **Confirm the generation target.** For multi-config builders, require the
   exact dataset/config/version. Avoid accidental "all configs" builds.
2. **Choose runner and storage.** Direct runner is for tiny local tests. Use a
   distributed runner for terabyte-scale datasets. Dataflow jobs should usually
   write TFDS data to a `gs://.../tensorflow_datasets` root and use a GCS temp
   and staging area.
3. **Build pipeline options safely.** Use
   [`scripts/beam_options_helper.py`](scripts/beam_options_helper.py) to create
   or validate `--beam_pipeline_options` strings and get warnings without
   launching Beam.
4. **Pass options through TFDS.** See
   [`references/beam-workflows.md`](references/beam-workflows.md) for CLI and
   programmatic examples.
5. **Set deterministic-order policy.** Default Beam writing preserves TFDS's
   deterministic ordering contract. Use `nondeterministic_order=True` or
   `--nondeterministic_order` only when faster unordered output is acceptable
   and downstream code never depends on example order.
6. **Control storage format and shards.** See
   [`references/performance-and-storage.md`](references/performance-and-storage.md)
   for `--file_format`, `--num_shards`, `--max_shard_size_mb`, and
   `DownloadConfig` equivalents.
7. **Tune readers after generation.** Prefer `shuffle_files=True` for large
   training datasets, tune `ReadConfig` for distributed workers and memory, skip
   unused or expensive features, and benchmark the final pipeline.
8. **Triage failures before rerunning expensive jobs.** Use
   [`references/troubleshooting.md`](references/troubleshooting.md) for Beam,
   GCS, sharding, determinism, and performance symptoms.

## Safe command skeletons

Local smoke only:

```bash
tfds build DATASET[/CONFIG] \
  --max_examples_per_split=10 \
  --data_dir=/tmp/tfds-smoke
```

Dataflow option construction without launching a job:

```bash
python scripts/beam_options_helper.py \
  --runner DataflowRunner \
  --dataset DATASET \
  --project GCP_PROJECT \
  --gcs-bucket gs://BUCKET \
  --requirements-file /tmp/beam_requirements.txt \
  --print-build-command
```

Programmatic generation:

```python
import apache_beam as beam
import tensorflow_datasets as tfds

flags = [
    "--runner=DataflowRunner",
    "--project=GCP_PROJECT",
    "--staging_location=gs://BUCKET/binaries",
    "--temp_location=gs://BUCKET/temp",
    "--requirements_file=/tmp/beam_requirements.txt",
]

download_config = tfds.download.DownloadConfig(
    beam_options=beam.options.pipeline_options.PipelineOptions(flags=flags),
    # Only set when unordered output is acceptable:
    # nondeterministic_order=True,
)
builder = tfds.builder("DATASET/CONFIG", data_dir="gs://BUCKET/tensorflow_datasets")
builder.download_and_prepare(download_config=download_config)
```

## Verification expectations

For this sub-skill, safe verification should avoid full downloads and cloud job
launches unless the user explicitly grants budget and credentials. Prefer:

- `python scripts/beam_options_helper.py --help` and representative option
  construction checks.
- Import/signature checks for `tfds.download.DownloadConfig`, `tfds.ReadConfig`,
  and `tfds.beam.ReadFromTFDS` in an environment that has the required optional
  packages.
- Tiny local Beam/dummy-data checks only when Apache Beam and TensorFlow are
  already installed.
- Documentation of skipped Dataflow/Flink/private-GCS checks as external-service
  gaps, not failures of local validation.
