# Dataset, file IO, and configuration API reference

This reference distills source evidence from ModelScope dataset, fileio, config, and tests into operational guidance. It is self-contained for future agents and does not require opening the original repository.

## `MsDataset.load` decision table

`MsDataset.load(dataset_name, ...)` accepts a string or a Python list.

| Source mode | Minimal call | Key notes |
|---|---|---|
| Inline list | `MsDataset.load(["a", "b"], target="text")` | A list is converted to a one-column Hugging Face `Dataset` and then wrapped. If `target` is omitted ModelScope uses `target`. Iteration yields target values when `target` is set. |
| Local single file | `MsDataset.load("data/train.csv")` | Existing local paths are routed through the Hugging Face data loader. Direct single-file extension routing covers `csv`, `tsv`, `json`, `jsonl`, `parquet`, and `txt`. |
| Local directory | `MsDataset.load("data_dir/")` | A local directory is passed to the local HF loader. For packaged loaders such as `imagefolder`, call `MsDataset.load("imagefolder", data_dir="images")`. |
| Packaged local builder | `MsDataset.load("csv", data_files={"train": "train.csv"})` | Use when the builder name is not a path. `data_files` must be non-empty. |
| Hugging Face Hub | `MsDataset.load("glue", subset_name="sst2", split="train", hub=Hubs.huggingface)` | Requires network and the `datasets`/HF stack. `use_streaming=True` forwards to Hugging Face streaming. |
| ModelScope Hub | `MsDataset.load("namespace/dataset", split="train")` or `MsDataset.load("dataset", namespace="namespace")` | Requires network. A relative `namespace/name` is split into `namespace` and `dataset_name` unless loading from Hugging Face. |
| Metadata discovery | `MsDataset.load("namespace/dataset", dataset_info_only=True)` | For general ModelScope datasets, returns a dict keyed by config/subset with available split-like entries when discoverable. Does not return examples. |
| Streaming | `MsDataset.load("namespace/dataset", split="train", use_streaming=True)` | Returns an iterable dataset or dict of iterable datasets. Avoid assumptions about length, random access, or full download. |

### Parameters to choose deliberately

- `dataset_name`: string path/name or Python list. For ModelScope Hub, `namespace/dataset` or a separate `namespace` are both supported. For local files, the path must exist before the load.
- `namespace`: ModelScope namespace. Default is the SDK's default dataset namespace. Needed for many ModelScope Hub loads unless encoded as `namespace/dataset`.
- `hub`: accepts ModelScope or Hugging Face enum/string values. ModelScope is the default. Use `Hubs.huggingface` for Hugging Face Hub names.
- `target`: single column to yield when iterating a wrapped `MsDataset`. Constructor validation requires the target to exist in dataset features. For inline list mode, the column is created.
- `version`: ModelScope revision or Hugging Face revision.
- `subset_name`: Hugging Face `name`/config or ModelScope subset/config.
- `split`: split name such as `train`, `validation`, `test`, or a Hugging Face split expression.
- `data_dir`: directory passed to a local/HF dataset builder, for example with `imagefolder`.
- `data_files`: string, sequence, or mapping from split to path/pattern(s). It must be non-empty if provided.
- `download_mode`: ModelScope `DownloadMode.REUSE_DATASET_IF_EXISTS` or `DownloadMode.FORCE_REDOWNLOAD`, or equivalent string values such as `reuse_dataset_if_exists` / `force_redownload`.
- `cache_dir`: local cache root for downloaded/prepared datasets. Prefer a user-chosen project cache, not a hardcoded checkout path.
- `features`: optional Hugging Face `Features` schema passed through to the loader.
- `use_streaming`: ModelScope's streaming flag. Use this name, not `streaming`, when calling `MsDataset.load`.
- `stream_batch_size`: ModelScope streaming batch size for ModelScope-native flows.
- `custom_cfg`: optional `Config` used to convert a loaded dataset to a task-specific custom dataset. This can require PyTorch and task/model config fields.
- `token`: authenticates with Hub APIs. Do not echo real tokens into logs or skill files.
- `dataset_info_only`: returns discoverable config/split information instead of loading examples for general datasets.
- `trust_remote_code`: explicit opt-in for remote or local Python dataset scripts. Leave false unless the code source is trusted.
- `**config_kwargs`: forwarded to the underlying builder. Keep this clean; avoid passing `streaming=` because `MsDataset.load` already forwards `use_streaming` as the underlying `streaming` argument.

### Return shapes

- Local/HF/ModelScope loads may return an `MsDataset`, a dict of split/config names to `MsDataset`, a Hugging Face `Dataset`/`DatasetDict` for Hugging Face Hub mode, a native iterable dataset, or a metadata dict for `dataset_info_only`.
- When `use_streaming=True`, expect an iterable-style object. Check examples with `next(iter(ds))`; avoid `len(ds)` and random indexing unless you verified support.
- For wrapped non-streaming datasets, `ms_ds.to_hf_dataset()` exposes the underlying Hugging Face dataset for operations such as `select`, `map`, `rename_columns`, and `save_to_disk`.

## Local examples

### Inline list

```python
from modelscope.msdatasets import MsDataset

ds = MsDataset.load(["positive example", "negative example"], target="text")
print(next(iter(ds)))  # "positive example"
```

### Local CSV file

```python
from modelscope.msdatasets import MsDataset

ds = MsDataset.load("data/train.csv")
row = next(iter(ds))
print(row.keys())
```

### Local multi-split files

```python
from modelscope.msdatasets import MsDataset

ds = MsDataset.load(
    "csv",
    data_files={
        "train": "data/train.csv",
        "validation": "data/validation.csv",
    },
)
train = ds["train"] if isinstance(ds, dict) else ds
print(next(iter(train)))
```

### Local JSONL with split

```python
from modelscope.msdatasets import MsDataset

ds = MsDataset.load("json", data_files={"train": "data/train.jsonl"}, split="train")
print(next(iter(ds)))
```

### Local image folder

```python
from modelscope.msdatasets import MsDataset

ds = MsDataset.load("imagefolder", data_dir="images", split="train")
print(next(iter(ds)))
```

## Remote examples that require network

### ModelScope Hub metadata discovery

```python
from modelscope.msdatasets import MsDataset

info = MsDataset.load("owner/dataset_name", dataset_info_only=True)
print(info)  # typically {"default": ["train", "test"]} when discoverable
```

### ModelScope Hub split load

```python
from modelscope.msdatasets import MsDataset

ds = MsDataset.load("owner/dataset_name", split="train", cache_dir=".cache/modelscope-datasets")
print(next(iter(ds)))
```

### Hugging Face Hub streaming

```python
from modelscope.msdatasets import MsDataset
from modelscope.utils.constant import Hubs

ds = MsDataset.load(
    "glue",
    subset_name="sst2",
    split="train",
    hub=Hubs.huggingface,
    use_streaming=True,
)
print(next(iter(ds)))
```

## File IO APIs

ModelScope file IO supports JSON/YAML/YML through a storage abstraction.

```python
from modelscope.fileio import load, dump, dumps

obj = load("recipe.yaml")
yaml_text = dumps(obj, "yaml")
json_text = dump(obj, file=None, file_format="json")
dump(obj, "out/recipe.json")
```

Supported formats are `json`, `yaml`, and `yml`. If `file_format` is omitted for a path, it is inferred from the file extension. For `dump(obj, file=None, ...)`, `file_format` is required.

### Storage limitations

- Local paths support `read`, `read_text`, `write`, and `write_text`; write creates parent directories as needed.
- `http://` and `https://` paths support read-only access through `requests.get`. They do not support writes.
- `oss://` is declared but not implemented for read or write in this source version.
- Unsupported URI prefixes fail before format handling.
- File-like objects with `read`/`write` are supported by the format handlers.

## Config APIs

See `references/configuration.md` for full safety rules. Common calls:

```python
from modelscope.utils.config import Config

cfg = Config.from_file("configuration.yaml")
print(cfg.safe_get("dataset.train.file"))
cfg.merge_from_dict({"train.batch_size": 8, "model.backbone.depth": 18})
```

- `Config.from_file(path, trust_remote_code=False, model_dir=None)` supports `.py`, `.json`, `.yaml`, `.yml`.
- `Config.from_string(text, file_format)` supports `.py`, `.json`, `.yaml`, `.yml`; `.py` strings are caller-provided in-process content and are not gated in the same way as remote files.
- `safe_get("a.b[0].c", default=...)` returns a default rather than raising on missing keys.
- `merge_from_dict` accepts dot-separated paths and can merge list entries by index or by dict `type` fields.

## Deprecated dataset upload/delete helpers

`MsDataset.upload`, `clone_meta`, and `upload_meta` carry deprecation warnings in source. `upload` recommends git or `modelscope.hub.api.HubApi.upload_folder` / `upload_file`; `upload_meta` recommends git or `modelscope upload owner_name/repo_name ...`. Treat `MsDataset.delete` as a destructive Hub operation requiring authentication and permissions. For non-deprecated Hub upload/delete command mechanics, route to `../hub-and-cli/SKILL.md`.
