# Data formats, recipes, and local validation

This reference gives concrete local/offline data patterns for ModelScope dataset loading and for the bundled validation script.

## Supported local file extensions through `MsDataset.load`

When `dataset_name` is an existing local file, ModelScope maps these extensions to Hugging Face packaged builders:

| File extension | Builder used | Typical row shape |
|---|---|---|
| `.csv` | `csv` | Dict keyed by CSV header names. |
| `.tsv` | `csv` | Dict keyed by header names; pass delimiter/tab kwargs if needed. |
| `.json` | `json` | Dict/list according to JSON structure. |
| `.jsonl` | `json` | One JSON object per line. |
| `.parquet` | `parquet` | Dict keyed by parquet columns. |
| `.txt` | `text` | Usually a text field from the text builder. |

For a packaged builder, pass the builder name as `dataset_name` and files via `data_files`, for example `MsDataset.load("csv", data_files={"train": "train.csv"})`.

## `data_files` shapes

Use one of these shapes:

```python
# One file, builder infers split/default behavior.
MsDataset.load("csv", data_files="data/train.csv")

# Multiple files in one default config.
MsDataset.load("json", data_files=["data/a.jsonl", "data/b.jsonl"])

# Explicit split map.
MsDataset.load("parquet", data_files={
    "train": "data/train-*.parquet",
    "validation": ["data/valid-a.parquet", "data/valid-b.parquet"],
})
```

`data_files` must not be an empty string, empty list, or empty dict. Globs are accepted by the underlying data loader, but validate them before use so a typo does not silently prepare an empty dataset.

## Column selection and mapping

### `target`

`target` is a single-column iteration shortcut. If you load:

```python
ds = MsDataset.load(["cat", "dog"], target="label")
print(next(iter(ds)))  # "cat"
```

then iterating yields values from `label`, not row dicts. For non-list datasets, `target` must match an existing feature column. If unsure, first inspect one sample without `target`:

```python
ds = MsDataset.load("csv", data_files={"train": "data/train.csv"}, split="train")
first = next(iter(ds))
print(first.keys())
```

### Renaming columns

`MsDataset.remap_columns({"old": "new"})` resets formatting and returns the underlying Hugging Face dataset with renamed columns. It does not return an `MsDataset` wrapper. A portable pattern is:

```python
ms_ds = MsDataset.load("csv", data_files={"train": "data/train.csv"}, split="train")
hf_ds = ms_ds.remap_columns({"sentence": "text", "label_id": "label"})
print(hf_ds.column_names)
```

For dictionaries of split datasets, apply mapping to the split you need or iterate through splits. Validate that every mapping source column exists in a small sample/header before running a long job.

## Custom datasets with `custom_cfg`

`MsDataset.load(..., custom_cfg=cfg)` can convert a loaded dataset into a task-specific custom dataset. Evidence shows this path uses `Config.safe_get("dataset.train"/"dataset.val")`, task fields, optional preprocessors, and custom dataset builders. It may require PyTorch and task/model-specific dependencies. Use it only when you have a trusted ModelScope `Config` and a clear downstream task. If the next step is training/evaluation, route to `../training-and-evaluation/SKILL.md` after the data load.

Minimal shape for a custom config is task-dependent, but common ModelScope configs include:

```yaml
task: text-classification
model:
  type: text-classification
dataset:
  train:
    file: data/train.csv
  val:
    file: data/validation.csv
preprocessor:
  type: Tokenize
```

Do not assume this generic shape is sufficient for every task. Inspect `cfg.safe_get("dataset.train")`, `cfg.safe_get("dataset.val")`, `cfg.safe_get("task")`, and relevant preprocessor fields before converting.

## Offline dataset recipe schema

The bundled `scripts/validate_dataset_recipe.py` accepts JSON/YAML recipes. The recipe is intentionally a static validation format, not a ModelScope-owned config format.

Required top-level field:

- `dataset_name`: local file path, local directory path, or local/package builder name such as `csv`, `json`, `parquet`, `text`, `imagefolder`, `audiofolder`.

Optional top-level fields:

- `source`: `local`, `local-builder`, `packaged`, `hf`, or `modelscope`. The validator defaults to `local` for paths and packaged builder names. Remote sources are rejected unless `--allow-remote` is passed, and even then only statically checked.
- `data_dir`: local directory for packaged builders such as `imagefolder`.
- `data_files`: string, list of strings, or mapping from split to string/list.
- `split`, `subset_name`, `namespace`, `target`, `cache_dir`, `download_mode`, `use_streaming`, `stream_batch_size`, `dataset_info_only`, `trust_remote_code`.
- `hub`: `modelscope` or `huggingface` for runtime code generation. Remote hub values are not loaded by the validator.
- `config`: path to a JSON/YAML/YML/PY ModelScope config. `.py` requires recipe `trust_remote_code: true` and is still only statically checked.
- `column_mapping`: mapping from source column name to destination column name. The validator checks source columns when it can infer a header from CSV/TSV/JSONL/JSON.
- `expected_columns`: list of column names expected in local CSV/TSV/JSONL/JSON data.

Example local CSV recipe:

```yaml
source: local-builder
dataset_name: csv
data_files:
  train: data/train.csv
  validation: data/validation.csv
split: train
target: label
expected_columns: [text, label]
column_mapping:
  text: sentence
trust_remote_code: false
```

Example JSONL recipe:

```json
{
  "dataset_name": "json",
  "data_files": {"train": "data/train.jsonl"},
  "split": "train",
  "expected_columns": ["prompt", "response"],
  "use_streaming": false
}
```

Example image folder recipe:

```yaml
dataset_name: imagefolder
data_dir: images
split: train
trust_remote_code: false
```

Validate with:

```bash
python scripts/validate_dataset_recipe.py recipe.yaml
```

Useful flags:

- `--base-dir DIR`: resolve relative paths against a directory other than the recipe directory.
- `--allow-remote`: allow static remote recipe validation without network checks.
- `--strict-columns`: require `target`, `column_mapping` sources, and `expected_columns` to be verifiable from local headers/samples.
- `--json`: emit machine-readable results.

## Runtime code generation from a validated recipe

After validation passes, translate the recipe to explicit code rather than dynamically splatting unreviewed keys:

```python
from modelscope.msdatasets import MsDataset

ds = MsDataset.load(
    "csv",
    data_files={"train": "data/train.csv"},
    split="train",
    target="label",
    cache_dir=".cache/modelscope-datasets",
    trust_remote_code=False,
)
```

Avoid including recipe-only keys such as `expected_columns` in `MsDataset.load` calls. Avoid passing `streaming`; use `use_streaming`.

## File IO examples

### Load a JSON/YAML recipe

```python
from modelscope.fileio import load

recipe = load("recipe.yaml")
assert isinstance(recipe, dict)
```

### Dump without writing

```python
from modelscope.fileio import dump, dumps

json_text = dump({"ok": True}, file=None, file_format="json")
yaml_text = dumps({"ok": True}, "yaml")
```

### Dump to a local file

```python
from modelscope.fileio import dump

dump({"dataset_name": "csv", "data_files": {"train": "train.csv"}}, "out/recipe.yaml")
```

Only local writes are supported. HTTP/HTTPS reads can work but are network-bound and read-only; OSS storage is not implemented in this source version.
