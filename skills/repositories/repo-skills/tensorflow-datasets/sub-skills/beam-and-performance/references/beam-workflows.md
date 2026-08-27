# Beam Workflows

This reference distills TFDS Beam behavior for future agents. It does not depend
on the source repository docs or tests.

## Concepts

TFDS uses Apache Beam for datasets whose example generation is too large for one
machine. Beam is involved during **download and prepare**; reading an already
prepared dataset usually uses TFDS readers or `tf.data`, except when a separate
Beam pipeline uses `tfds.beam.ReadFromTFDS` as an input source.

Important boundaries:

- A Beam build can run locally with the Direct runner, but local full builds can
  require terabytes of disk/RAM and weeks of wall time.
- Dataflow, Flink, Spark, private GCS, and service-account usage are external
  systems. Validate commands and options locally, then ask for explicit approval
  before launching.
- `tfds build DATASET` may build all configs for a configurable dataset. Prefer
  `DATASET/CONFIG` or the relevant config flag when the dataset has configs.

## Existing Beam dataset: CLI flow

Local smoke:

```bash
tfds build DATASET[/CONFIG] \
  --max_examples_per_split=10 \
  --data_dir=/tmp/tfds-smoke
```

Dataflow-style command shape:

```bash
tfds build DATASET/CONFIG \
  --data_dir=gs://BUCKET/tensorflow_datasets \
  --beam_pipeline_options="runner=DataflowRunner,project=GCP_PROJECT,job_name=DATASET-gen,staging_location=gs://BUCKET/binaries,temp_location=gs://BUCKET/temp,requirements_file=/tmp/beam_requirements.txt"
```

Notes:

- TFDS parses `--beam_pipeline_options` as a comma-separated string and converts
  each `key=value` segment into a Beam pipeline flag.
- Do not include commas inside values; TFDS splits on commas.
- Use a requirements file on cloud workers. A common pattern is one line such as
  `tensorflow_datasets[DATASET]` or the matching nightly package if the dataset
  requires unreleased TFDS code. Add dataset-specific dependencies required by
  the builder.
- Prefer a GCS `data_dir` for Dataflow so workers can write prepared shards to a
  shared location.
- If publishing to a separate prepared-data location is requested, validate the
  target root and overwrite/skip policy before launching. Publishing can mutate
  remote storage.

Use the bundled helper for non-launching construction:

```bash
python scripts/beam_options_helper.py \
  --runner DataflowRunner \
  --dataset DATASET \
  --project GCP_PROJECT \
  --gcs-bucket gs://BUCKET \
  --requirements-file /tmp/beam_requirements.txt \
  --print-build-command
```

## Existing Beam dataset: programmatic flow

```python
import apache_beam as beam
import tensorflow_datasets as tfds

flags = [
    "--runner=DataflowRunner",
    "--project=GCP_PROJECT",
    "--job_name=dataset-gen",
    "--staging_location=gs://BUCKET/binaries",
    "--temp_location=gs://BUCKET/temp",
    "--requirements_file=/tmp/beam_requirements.txt",
]

beam_options = beam.options.pipeline_options.PipelineOptions(flags=flags)
download_config = tfds.download.DownloadConfig(beam_options=beam_options)
builder = tfds.builder("DATASET/CONFIG", data_dir="gs://BUCKET/tensorflow_datasets")
builder.download_and_prepare(download_config=download_config)
```

Relevant `DownloadConfig` controls:

- `beam_runner`: optional runner object/value forwarded to Beam.
- `beam_options`: a Beam `PipelineOptions` instance.
- `max_examples_per_split`: cap output examples for smoke tests.
- `num_shards`, `min_shard_size`, `max_shard_size`: prepared-shard controls.
- `nondeterministic_order`: allow unordered Beam writing for speed when exact
  example order is irrelevant.

## Flink runner shape

```bash
tfds build DATASET/CONFIG \
  --beam_pipeline_options="runner=FlinkRunner,flink_version=FLINK_VERSION,flink_conf_dir=FLINK_CONFIG_DIR"
```

Before using Flink, verify the installed Beam version is compatible with the
Flink version and that worker dependencies can import TFDS and the dataset's
extras.

## Authoring Beam-capable builders

Modern TFDS Beam authoring can use `tfds.core.GeneratorBasedBuilder` and return
Beam objects from `_generate_examples`:

```python
class MyDataset(tfds.core.GeneratorBasedBuilder):
    VERSION = tfds.core.Version("1.0.0")

    def _split_generators(self, dl_manager):
        paths = dl_manager.download_and_extract(...)
        return {"train": self._generate_examples(paths)}

    def _generate_examples(self, paths):
        beam = tfds.core.lazy_imports.apache_beam
        return (
            beam.Create(paths)
            | beam.Map(_process_one_file)
        )
```

Authoring rules:

- Prefer `tfds.core.lazy_imports.apache_beam` inside the builder so users can
  read already prepared data without installing Beam.
- `tfds.core.BeamBasedBuilder` exists but is deprecated; do not choose it for new
  code unless maintaining an old builder.
- Beam transforms and functions are serialized to workers. Avoid closures over
  mutable state, local non-picklable objects, open files, clients, or a large
  builder instance.
- Mutating builder metadata inside worker-side transforms will not reliably
  update the local `DatasetInfo`. Compute metadata through supported Beam
  aggregates before finalization.
- If `_split_generators(self, dl_manager, pipeline)` is declared, TFDS can pass
  the shared Beam pipeline so several splits can share upstream transforms.
- Use unique Beam labels when applying the same transform pattern to multiple
  splits.

## Deterministic vs nondeterministic output

Default TFDS Beam writing uses deterministic ordering. It sorts/partitions by
example key and preserves the reproducibility assumptions used by TFDS metadata
and tests.

Set `nondeterministic_order=True` only when:

- downstream consumers will shuffle and never depend on row order;
- exact reproducibility of example order is not an acceptance criterion;
- the user accepts that the dataset metadata records nondeterministic order; and
- you want the faster `NoShuffleBeamWriter` path for Beam PCollections.

CLI shape:

```bash
tfds build DATASET/CONFIG --nondeterministic_order --beam_pipeline_options="..."
```

Programmatic shape:

```python
download_config = tfds.download.DownloadConfig(
    beam_options=beam_options,
    nondeterministic_order=True,
)
```

Do not use nondeterministic order to mask duplicate keys, unstable feature
encoding, or missing deterministic tests.

## Reading prepared TFDS data inside Beam

Use `tfds.beam.ReadFromTFDS` when an independent Beam pipeline needs an already
prepared dataset as input:

```python
builder = tfds.builder("DATASET", data_dir="DATA_DIR")

_ = (
    pipeline
    | tfds.beam.ReadFromTFDS(builder, split="train", workers_per_shard=1)
    | beam.Map(tfds.as_numpy)
    | ...
)
```

Behavior and limitations:

- The dataset must already be generated; otherwise `ReadFromTFDS` raises an
  error that no examples were found.
- It creates work from split file instructions so shards can be processed in
  parallel.
- `workers_per_shard > 1` further splits file instructions, but TFRecord readers
  may still need to scan skipped records to reach their range.
- Subsplits using skip/take are supported only when `batch_size=None` is passed
  through to `builder.as_dataset`; `batch_size` plus a sliced split can raise
  `NotImplementedError`.

## Pre-launch checklist for external runners

Before starting Dataflow/Flink/Spark:

1. Dataset/config/version is exact; no accidental all-config build.
2. The package and dataset-specific extras will be installed on workers.
3. `data_dir`, temporary, and staging locations are writable by the worker
   identity and have enough quota.
4. The user has approved cloud costs and provided a credential boundary.
5. Checksum registration, overwrite/reuse, `max_examples_per_split`, shard
   controls, and deterministic-order policy are explicit.
6. A local non-launching command/options validation has passed.
