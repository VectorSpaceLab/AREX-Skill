# Loading Workflows

This reference gives task-first patterns for choosing `load_dataset`, `load_dataset_builder`, `load_from_disk`, Python object constructors, and packaged modules. Keep loading code separate from downstream transforms; route map/filter/shuffle/stream processing to `../../processing-streaming/SKILL.md`.

## Quick Decision Tree

| User has | Use | Key parameters | Notes |
| --- | --- | --- | --- |
| Hub dataset id | `load_dataset(path)` | `name`, `split`, `revision`, `token`, `streaming` | Network unless cached/offline-compatible. |
| Local CSV/JSON/Parquet/Text/etc. | `load_dataset("csv", ...)` or matching packaged module | `data_files`, `data_dir`, `split`, format-specific kwargs | Prefer explicit split mapping. |
| Directory with metadata or recognizable files | `load_dataset(local_dir)` or `load_dataset_builder(local_dir)` | `name`, `data_dir`, `data_files` | Inspect first if configs are ambiguous. |
| Saved dataset snapshot | `load_from_disk(path)` | `keep_in_memory`, `storage_options` | Path must be a `save_to_disk` output, not raw CSV/JSON. |
| Python rows or columns | `Dataset.from_dict/list/pandas/generator` | `features`, `split`, `gen_kwargs`, `num_proc` | Best for programmatic construction. |
| Need configs/splits/features before rows | `load_dataset_builder(...)` | Same load context except `split`, `streaming`, `num_proc` | Use builder metadata and `download_and_prepare` selectively. |

## Hub Datasets

Start with the most constrained request:

```python
from datasets import load_dataset

ds = load_dataset(
    "namespace/dataset_name",
    name="subset_or_config",      # omit when there is one default config
    split="train",                # omit to get DatasetDict for all available splits
    revision="main",              # branch, tag, or commit hash
    token=True,                    # use authenticated local Hub session if needed
)
```

Guidance:

- Use `load_dataset_builder("namespace/name", name=...)` first when the user asks what configs, splits, or features exist.
- Set `revision` to a branch, tag, or commit hash for reproducible Hub loads and to diagnose invalid-revision failures.
- Use `token=True` only for private/gated datasets when local authentication is already configured. Do not echo token values in logs or generated snippets.
- Treat `streaming=True` as a loading-mode choice that changes the returned dataset type and defers row materialization; route detailed streaming iteration and transformations to `../../processing-streaming/SKILL.md`.
- If the environment is offline, only cached Hub datasets and cached revisions can work. Diagnose without forcing network unless the user explicitly permits it.

## Local Files and Directories

For local tabular or text data, choose a packaged module explicitly when possible:

```python
from datasets import Features, Value, load_dataset

features = Features({"text": Value("string"), "label": Value("int64")})
data_files = {
    "train": "data/train/*.csv",
    "validation": "data/validation/*.csv",
    "test": "data/test.csv",
}

ds = load_dataset(
    "csv",
    data_files=data_files,
    split="train",
    features=features,
)
```

Practical rules:

- Use `data_files={"train": ..., "validation": ..., "test": ...}` when split names matter. A string or list without a mapping usually loads into or infers a `train` split.
- Use `split="train"` to get a single `Dataset`; omit `split` to receive a `DatasetDict` keyed by available splits.
- Use `data_dir` to point at a subdirectory inside a dataset repository or local dataset directory; use `data_files` to select specific files or globs.
- Pass format-specific kwargs through `load_dataset`, such as CSV separators or JSON `field`, when the packaged module supports them.
- For remote URLs in `data_files`, treat loading as network access and consider `streaming=True` for large files.
- For files on S3, GCS, or other fsspec filesystems, pass `storage_options` required by that filesystem; never hard-code secrets.

Common packaged modules include `csv`, `json`, `parquet`, `text`, `arrow`, `imagefolder`, `audiofolder`, `videofolder`, `webdataset`, `hdf5`, `sql`, `pandas`, `spark`, `xml`, and related folder-based builders. Optional media or framework dependencies may be required for some modules; do not assume they are installed.

## Local Packaged Modules and Dataset Directories

A local directory can be loaded directly when it contains a supported data layout, metadata, or dataset module files:

```python
from datasets import load_dataset_builder

builder = load_dataset_builder("path/to/local_dataset", name="config_name")
print(builder.config.name)
print(builder.info.features)
print(builder.info.splits)
```

Use this pattern when:

- The directory advertises multiple configs and the user did not choose one.
- Split inference might be wrong because file names do not include `train`, `test`, or `validation`.
- Metadata declares `data_files`, and you need to confirm how they resolve before loading.
- The local path contains custom loading code. Be explicit about trust and security when code execution is involved; do not enable remote/custom code casually.

## Disk Snapshots

Use `load_from_disk` only for a directory produced by `Dataset.save_to_disk` or `DatasetDict.save_to_disk`:

```python
from datasets import load_from_disk

ds_or_dict = load_from_disk("path/to/saved_dataset")
```

If the path points at raw CSV, JSON, Parquet, or text files, use `load_dataset` with a packaged module instead. For remote filesystem snapshots, pass `storage_options` suitable for that filesystem and keep credentials outside code.

## Python Object Construction

Use constructors for data already in memory or produced by application code:

```python
from datasets import Dataset, DatasetDict

train = Dataset.from_list([
    {"text": "great", "label": 1},
    {"text": "bad", "label": 0},
])

test = Dataset.from_dict({"text": ["ok"], "label": [1]})

ds = DatasetDict({"train": train, "test": test})
```

Use `Dataset.from_generator(generator, gen_kwargs=..., features=..., num_proc=...)` when rows are generated lazily by Python code but should become an in-memory or cached `Dataset`. Put schema design in `../../features-formats/SKILL.md` when the user needs detailed feature typing or media decoding choices.

## Fixture for Verification

The helper `../scripts/create_local_loading_fixture.py` creates a small deterministic directory:

```bash
python ../scripts/create_local_loading_fixture.py --output /tmp/datasets-loading-fixture --print-example
```

It writes `train.csv`, `validation.csv`, and `test.csv` with columns suited to explicit `Features` examples. Use it for offline-safe checks of local CSV loading and split selection.
