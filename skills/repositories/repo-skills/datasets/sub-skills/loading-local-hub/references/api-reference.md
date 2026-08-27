# Loading API Reference

This reference summarizes loading APIs verified for package version `5.0.1.dev0`. It focuses on parameters that affect source selection, splits, configs, network/auth, storage, and object construction.

## `load_dataset`

Signature shape:

```python
load_dataset(
    path,
    name=None,
    data_dir=None,
    data_files=None,
    split=None,
    cache_dir=None,
    features=None,
    download_config=None,
    download_mode=None,
    verification_mode=None,
    keep_in_memory=None,
    save_infos=False,
    revision=None,
    token=None,
    streaming=False,
    num_proc=None,
    storage_options=None,
    **config_kwargs,
)
```

Parameter guidance:

| Parameter | Use it for | Common mistakes |
| --- | --- | --- |
| `path` | Hub dataset id, local dataset directory, or packaged module name such as `csv` | Passing a raw file path as `path` when a packaged module plus `data_files` is clearer. |
| `name` | Builder config/subset name | Omitting it for multi-config datasets or using a split name as config. |
| `data_dir` | Subdirectory relative to Hub/local base path | Using it when exact file globs belong in `data_files`. |
| `data_files` | Specific files, globs, URLs, or split mapping | Relying on split inference when deterministic train/test/validation names are required. |
| `split` | Return one split as `Dataset` or `IterableDataset` | Omitting it and then treating returned `DatasetDict` as a single dataset. |
| `features` | Provide expected schema at load time | Use `../../features-formats/SKILL.md` for nontrivial schema/casting details. |
| `revision` | Hub branch, tag, or commit | Expecting uncached revisions to load offline. |
| `token` | Private/gated Hub access | Printing secrets or using token when the dataset is public. |
| `streaming` | Avoid full materialization during load | Applying normal eager-only transforms; route to `../../processing-streaming/SKILL.md`. |
| `num_proc` | Parallel preparation for compatible builders | Assuming every source benefits or supports it. |
| `storage_options` | fsspec-backed local/remote filesystems | Hard-coding credentials or forgetting to pass options to remote files. |
| `**config_kwargs` | Format/builder-specific options such as CSV dialect or JSON field | Passing options that belong to a different packaged module. |

Return behavior:

- `split=None` generally returns a `DatasetDict` or `IterableDatasetDict` when multiple splits are available.
- `split="train"` returns a single `Dataset` or `IterableDataset`.
- `streaming=True` returns iterable variants and often avoids downloading all data up front.

## Builder Inspection

Use `load_dataset_builder` before materializing rows:

```python
from datasets import load_dataset_builder

builder = load_dataset_builder(
    "csv",
    data_files={"train": "data/train/*.csv", "test": "data/test.csv"},
)
print(builder.config.name)
print(builder.info.features)
print(builder.info.splits)
```

Signature shape is similar to `load_dataset` but without `split`, `streaming`, and `num_proc`. It returns a `DatasetBuilder`.

Useful builder properties and methods:

| Item | Use |
| --- | --- |
| `builder.config` | Confirm selected config name and resolved `data_files`. |
| `builder.info` | Inspect description, features, homepage, citation, and split metadata when available. |
| `builder.info.features` | Check inferred or declared schema before loading rows. |
| `builder.info.splits` | Check known splits after metadata/preparation information exists. |
| `builder.download_and_prepare(...)` | Prepare data explicitly when needed; may access network or filesystem depending on source. |
| `builder.as_dataset(split=...)` | Build a dataset from prepared data. |
| `builder.as_streaming_dataset(split=...)` | Build iterable streaming dataset; route downstream streaming operations to `../../processing-streaming/SKILL.md`. |

For multi-config datasets, list or infer valid config names from builder metadata or error messages, then retry with `name="..."`. Do not guess that `default` exists.

## Disk Snapshots

`load_from_disk(dataset_path, keep_in_memory=None, storage_options=None)` reloads snapshots created by `save_to_disk`:

```python
from datasets import load_from_disk

snapshot = load_from_disk("saved/my_dataset")
```

Guidance:

- Use it for previously serialized `Dataset` or `DatasetDict` directories, not raw source files.
- If the directory contains Arrow data and dataset metadata from `save_to_disk`, `load_from_disk` is appropriate.
- If the path contains files such as `train.csv`, `data.jsonl`, or `part-000.parquet`, use `load_dataset` with `csv`, `json`, or `parquet`.
- Pass `storage_options` when the snapshot is on a remote filesystem that requires fsspec options.

## Python Object Loaders

Construct datasets without file or Hub loading when rows already exist in Python:

| API | Best for | Key parameters |
| --- | --- | --- |
| `Dataset.from_dict(mapping, features=None, info=None, split=None, on_mixed_types=None)` | Column-oriented Python data | Every column should have consistent length. |
| `Dataset.from_list(list_of_dicts, features=None, info=None, split=None)` | Row-oriented records | Keys should be consistent across rows for predictable schema. |
| `Dataset.from_pandas(df, features=None, info=None, split=None, preserve_index=None)` | Pandas DataFrame input | Optional pandas dependency is required; index handling can affect columns. |
| `Dataset.from_generator(generator, features=None, cache_dir=None, keep_in_memory=False, gen_kwargs=None, num_proc=None, split="train", fingerprint=None, **kwargs)` | Programmatic row generation | Generator must yield examples; use `gen_kwargs` for inputs. |
| `DatasetDict({"train": ds, ...})` | Grouping split datasets | Values should be `Dataset` objects with compatible intended usage. |

Generator example:

```python
from datasets import Dataset


def records(prefix):
    for idx in range(3):
        yield {"id": idx, "text": f"{prefix}-{idx}"}


ds = Dataset.from_generator(records, gen_kwargs={"prefix": "row"}, split="train")
```

## Packaged Module Notes

Use packaged modules when the source format is known. Common examples:

- `csv`: CSV/TSV and delimiter-based tabular data; pass CSV-specific kwargs such as `sep` when needed.
- `json`: JSON or JSON Lines; pass `field` when records are nested under a top-level key.
- `parquet` and `arrow`: columnar local or remote files.
- `text`: plain text files, one example per line or file depending options.
- Folder/media builders such as `imagefolder`, `audiofolder`, `videofolder`, `webdataset`, and `meshfolder`: useful for directory layouts, but may require optional decoding dependencies.
- `hdf5`, `sql`, `pandas`, `spark`, `xml`, and related modules: use only when their dependencies and source shape match the task.

For detailed schema and decoding decisions, link the caller to `../../features-formats/SKILL.md` rather than duplicating feature guidance here.
