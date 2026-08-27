# Troubleshooting dataset, file IO, and config workflows

## `ModuleNotFoundError` or import errors before data loading

ModelScope imports may require optional dependencies from dataset or Hub stacks. The dataset requirement evidence includes `datasets`, `addict`, `attrs`, `einops`, `Pillow`, `python-dateutil`, `scipy`, `simplejson`, `sortedcontainers`, `urllib3`, and OSS-related packages. Install only the minimum dependency set for your workflow. If the import problem is broad package setup, use the root ModelScope skill or environment guidance rather than patching code.

## `dataset_name must be str or list`

`MsDataset.load` accepts only a string or a Python list. Convert `pathlib.Path` to `str` first:

```python
MsDataset.load(str(path_obj))
```

For structured local recipes, do not pass the whole recipe dict as `dataset_name`; unpack reviewed fields into explicit arguments.

## Local file or directory not found

`MsDataset.load` routes to local loading only when `os.path.exists(dataset_name)` is true or when `dataset_name` is a packaged builder such as `csv`. For local recipes:

- Resolve paths relative to the recipe file or a known project root.
- Validate `data_files` globs expand to at least one file.
- Use `python scripts/validate_dataset_recipe.py recipe.yaml` before loading.

## Empty or invalid `data_files`

The underlying data loader rejects empty `data_files`. Check for:

- Empty string: `data_files: ""`
- Empty list: `data_files: []`
- Empty mapping: `data_files: {}`
- Split key mapped to empty list or missing glob matches

Use a non-empty path, list, or split map.

## Unsupported file extension or file IO format

File IO `load/dump/dumps` supports only `json`, `yaml`, and `yml`. Dataset single-file routing supports local `csv`, `tsv`, `json`, `jsonl`, `parquet`, and `txt`. These are different format sets.

Examples:

- `modelscope.fileio.load("data.csv")` fails: CSV is not a fileio config format.
- `MsDataset.load("data.yaml")` is not a supported single-file dataset loader.
- `Config.from_file("config.toml")` fails: only `.py`, `.json`, `.yaml`, `.yml` are supported.

## HTTP, HTTPS, and OSS limitations

File IO can read `http://` and `https://` through `requests.get`, but writes are not supported. OSS storage is declared but not implemented in this source version. Dataset loading from remote Hubs is separate from file IO and may require Hub credentials, network access, and cache directories.

## `streaming` argument conflicts

Use `use_streaming=True` with `MsDataset.load`. The method forwards that value to the underlying Hugging Face loader as `streaming=use_streaming`. Passing an extra `streaming=` in `**config_kwargs` can collide with the forwarded keyword or create confusing behavior.

Correct:

```python
MsDataset.load("csv", data_files={"train": "train.csv"}, use_streaming=True)
```

Avoid:

```python
MsDataset.load("csv", data_files={"train": "train.csv"}, streaming=True)
```

## Streaming object surprises

When `use_streaming=True`, the return may be iterable-only. Avoid `len(ds)`, random indexing, `.select(...)`, or operations that require materialized data. Test with:

```python
sample = next(iter(ds))
```

If a training workflow needs DataLoader parallelism, handle that in the training/evaluation sub-skill.

## `dataset_info_only` returned empty or unexpected data

`dataset_info_only=True` is best for general ModelScope datasets and local script metadata discovery. Some builders have limited metadata; the code falls back through builder configs, `info.splits`, and dry-run split discovery. Empty values can mean the dataset has no discoverable split metadata, not necessarily that the dataset is empty.

## Split not found

If a split is not available, inspect metadata first when remote access is allowed:

```python
info = MsDataset.load("owner/dataset", dataset_info_only=True)
print(info)
```

For local recipes, compare `split` to the keys in `data_files`. If `data_files` is `{"validation": "valid.csv"}`, `split="val"` is likely wrong.

## Target column errors

The `target` column must exist in dataset features for wrapped datasets. For local CSV/JSONL, inspect headers or first records. The validator can catch many cases:

```bash
python scripts/validate_dataset_recipe.py recipe.yaml --strict-columns
```

If target is only needed for later training, consider loading row dicts first and route feature/label selection to `../training-and-evaluation/SKILL.md`.

## Column mapping did not return an `MsDataset`

`MsDataset.remap_columns` returns the underlying Hugging Face dataset directly. This is expected. If later code expects an `MsDataset`, either wrap again when appropriate or continue with Hugging Face dataset APIs.

## `Refusing to load Python config` or remote-code warnings

This is a safety gate. Do not bypass it by default. Options:

1. Prefer JSON/YAML config or dataset scripts when available.
2. Inspect the `.py` file out-of-band if permitted, then ask for explicit trust.
3. Only after trust is established, pass `trust_remote_code=True` to `Config.from_file` or `MsDataset.load`.

Never set `trust_remote_code=True` just to silence a warning.

## YAML parsing surprises

ModelScope's YAML handler uses `yaml.safe_load` for loading. Empty YAML files load as `None`, not `{}`. Validate recipes require a mapping at the top level.

## Deprecated upload/delete workflows

`MsDataset.upload`, `clone_meta`, and `upload_meta` are deprecated in source. `MsDataset.delete` is destructive and requires Hub permissions. For current upload/delete command mechanics, authentication, and CLI alternatives, route to `../hub-and-cli/SKILL.md`.
