# Datasets API Surface

This reference records the public API facts verified during skill creation. Use the focused sub-skills for deeper workflows and troubleshooting.

## Loading and Creation

- `load_dataset(path, name=None, data_dir=None, data_files=None, split=None, cache_dir=None, features=None, download_config=None, download_mode=None, verification_mode=None, keep_in_memory=None, save_infos=False, revision=None, token=None, streaming=False, num_proc=None, storage_options=None, **config_kwargs)` loads Hub datasets, local dataset repos, and supported local file formats.
- `load_dataset_builder(path, name=None, data_dir=None, data_files=None, cache_dir=None, features=None, download_config=None, download_mode=None, revision=None, token=None, storage_options=None, **config_kwargs)` returns a builder for inspection, preparation, or streaming dataset construction.
- `load_from_disk(dataset_path, keep_in_memory=None, storage_options=None)` reloads a `Dataset` or `DatasetDict` written with `save_to_disk`.
- `Dataset.from_dict`, `Dataset.from_list`, `Dataset.from_pandas`, and `Dataset.from_generator` create datasets from in-memory or generated Python data.

## Processing and Streaming

- `Dataset.map(...)` supports `batched`, `batch_size`, `remove_columns`, `features`, `num_proc`, cache controls, fingerprints, and mixed-type handling.
- `Dataset.filter`, `select`, `shuffle`, `train_test_split`, `cast`, `cast_column`, `rename_column`, and `remove_columns` are core map-style transforms.
- `IterableDataset.map`, `filter`, and `shuffle(buffer_size=...)` support streaming-style workflows without map-style random access or cache semantics.
- `concatenate_datasets` and `interleave_datasets` combine map-style or iterable datasets; iterable shard behavior differs from eager Arrow datasets.
- `set_format` and `with_format` control row materialization for NumPy, pandas, PyTorch, TensorFlow, JAX, Polars, or Arrow integrations when the needed framework is installed.

## Features and Formats

- `Features` maps column names to feature types such as `Value`, `ClassLabel`, `Sequence`, `List`, `LargeList`, array features, `Translation`, and `Json`.
- `Audio(sampling_rate=None, decode=True, num_channels=None, stream_index=None)`, `Image(mode=None, decode=True)`, `Video(decode=True, stream_index=None, dimension_order='NCHW', num_ffmpeg_threads=1, device='cpu', seek_mode='exact')`, `Pdf(decode=True)`, `Nifti(decode=True)`, and `Mesh(...)` describe multimodal columns and may require optional extras.
- Supported packaged loaders include common tabular/text/Arrow formats and folder-style media datasets; route loader-specific choices to `../sub-skills/features-formats/SKILL.md`.

## Sharing, CLI, and Cache

- `Dataset.push_to_hub(repo_id, config_name='default', set_default=None, split=None, data_dir=None, commit_message=None, commit_description=None, private=None, token=None, revision=None, create_pr=False, max_shard_size=None, num_shards=None, embed_external_files=True, num_proc=None)` uploads a dataset split/config to the Hub.
- `DatasetDict.push_to_hub` has analogous repository/config/sharding arguments for multiple splits.
- `datasets-cli` exposes `env`, `test`, and `delete_from_hub`; only `env` and `--help` checks are non-mutating by default.
