# TensorFlow Datasets API Overview

Use this reference when choosing the correct TFDS surface before routing into a sub-skill. Detailed workflows live under the nearest sub-skill references.

## Package identity

- Distribution: `tensorflow-datasets` (nightly builds may use `tfds-nightly`).
- Import: `import tensorflow_datasets as tfds`.
- CLI entry point: `tfds`.
- Core purpose: deterministic download/prepare/read workflows for public and custom datasets, exposed as `tf.data.Dataset`, Python/NumPy data sources, prepared dataset directories, and metadata-rich builders.

## Public entry point map

| Task | Primary API or command | Route |
|---|---|---|
| Load an existing dataset as `tf.data.Dataset` | `tfds.load(...)` or `tfds.builder(...).as_dataset(...)` | `sub-skills/data-loading/` |
| Inspect dataset metadata without downloading | `tfds.builder(name, data_dir=..., try_gcs=...)` | `sub-skills/data-loading/` |
| Use TFDS from NumPy/JAX/PyTorch-style code | `tfds.data_source(...)`, `tfds.as_numpy(...)` | `sub-skills/data-loading/` |
| Split/slice deterministic subsets | split strings, `tfds.even_splits`, `tfds.split_for_jax_process` | `sub-skills/data-loading/` |
| Author a new dataset builder | `tfds.core.GeneratorBasedBuilder`, `DatasetInfo`, `BuilderConfig`, `Version`, `SplitGenerator` | `sub-skills/dataset-authoring/` |
| Define feature schemas | `tfds.features.FeaturesDict`, `Image`, `ClassLabel`, `Text`, `Sequence`, `Tensor`, `Audio`, `Video`, `BBoxFeature` | `sub-skills/dataset-authoring/` |
| Test a custom builder | `tfds.testing.DatasetBuilderTestCase`, dummy data, checksum files | `sub-skills/dataset-authoring/` |
| Build or scaffold from the CLI | `tfds build`, `tfds new` | `sub-skills/cli-workflows/` |
| Convert prepared dataset file formats | `tfds convert_format` | `sub-skills/cli-workflows/` plus `sub-skills/formats-and-community/` |
| Build from Croissant JSON-LD | `tfds build_croissant`, `CroissantBuilder` | `sub-skills/formats-and-community/` and CLI syntax in `sub-skills/cli-workflows/` |
| Load an external prepared directory | `tfds.builder_from_directory`, `tfds.builder_from_directories` | `sub-skills/formats-and-community/` |
| Use folder datasets | `tfds.ImageFolder`, `tfds.TranslateFolder` | `sub-skills/formats-and-community/` |
| Use community/HuggingFace namespaces or dataset collections | community registry APIs, `tfds.dataset_collection(...)` | `sub-skills/formats-and-community/` |
| Scale generation with Beam/Dataflow/Flink/GCS | `tfds.core.BeamBasedBuilder`, `DownloadConfig(beam_options=...)`, `tfds build --beam_pipeline_options` | `sub-skills/beam-and-performance/` |
| Tune read/generation performance | `ReadConfig`, file format, sharding, cache/batch/prefetch order | `sub-skills/beam-and-performance/` and `sub-skills/data-loading/` |

## Verified signatures worth preserving

The prepared inspection environment verified these public signatures. Use sub-skill references for explanations and examples.

```python
tfds.load(name, *, split=None, data_dir=None, batch_size=None,
          shuffle_files=False, download=True, as_supervised=False,
          decoders=None, read_config=None, with_info=False,
          builder_kwargs=None, download_and_prepare_kwargs=None,
          as_dataset_kwargs=None, try_gcs=False, file_format=None)

tfds.builder(name, *, try_gcs=False, **builder_kwargs)
tfds.data_source(name, *, split=None, data_dir=None, download=True,
                 decoders=None, deserialize_method=..., builder_kwargs=None,
                 download_and_prepare_kwargs=None, try_gcs=False)
tfds.builder_from_directory(builder_dir, file_format=None)
tfds.builder_from_directories(builder_dirs, *, filetype_suffix=None)
tfds.even_splits(split, n, *, drop_remainder=False)
```

Important classes:

```python
tfds.core.DatasetBuilder(*, data_dir=None, config=None, version=None)
tfds.core.GeneratorBasedBuilder(*, file_format=None, **kwargs)
tfds.core.BuilderConfig(name, version=None, release_notes=None,
                        supported_versions=..., description=None, tags=...)
tfds.core.Version(version, experiments=None, tfds_version_to_prepare=None)
tfds.download.DownloadConfig(..., max_examples_per_split=None,
                             beam_runner=None, beam_options=None,
                             num_shards=None, max_shard_size=1073741824,
                             nondeterministic_order=False)
```

Feature connector constructor examples:

```python
tfds.features.FeaturesDict(mapping)
tfds.features.Image(shape=None, dtype=None, encoding_format=None)
tfds.features.ClassLabel(num_classes=None, names=None, names_file=None)
tfds.features.Sequence(feature, length=None)
tfds.features.Text(encoder=None, encoder_config=None)
tfds.features.Tensor(shape=..., dtype=..., optional=False)
```

## Optional dependency matrix

| Dependency | Needed for | Notes |
|---|---|---|
| `tensorflow` or `tensorflow-cpu` | `tf.data` reading, `ReadConfig` TensorFlow types, Keras examples, some CLI import paths | The base package can import without TensorFlow for some workflows, but practical CLI/data reading commonly needs it. |
| `apache-beam` | Beam builders, Dataflow/Flink workflows, `convert_format` Beam helpers | Install only when Beam workflows are selected. Worker environments need the same relevant dependencies. |
| `mlcroissant` | `tfds build_croissant` and CroissantBuilder | Required for Croissant JSON-LD workflows. |
| `datasets` | HuggingFace community wrapper | Do not install just to load ordinary packaged TFDS datasets. |
| `pandas`, `scipy`, `Pillow`, `pydub`, `gcsfs`, `zarr`, `tensorflow-io`, others | Specific dataset builders | Install per selected dataset or documented extra, not all extras. |
| Cloud credentials / GCS access | Private GCS, publishing, Dataflow staging/temp, some public-bucket access checks | Treat credentials and cloud writes as user-authorized external operations. |

## Safe first checks

From a public package environment:

```bash
python - <<'PY'
import tensorflow_datasets as tfds
print(tfds.__version__)
print(tfds.builder('mnist').info.features)
print(tfds.even_splits('train', 3))
PY
```

If CLI workflows are relevant:

```bash
tfds --version
tfds --help
```

For a broader environment probe, run `scripts/check_tfds_environment.py --check-cli` from the root of this skill directory.
