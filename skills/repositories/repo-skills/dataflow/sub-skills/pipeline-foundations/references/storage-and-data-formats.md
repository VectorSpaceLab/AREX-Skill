# Storage and data format reference

DataFlow storage objects are the bridge between operators. The safest offline default is `FileStorage` with a tiny local JSONL fixture.

## Step model

All file-like storages start with `operator_step = -1`.

- `storage.step()` increments the counter and returns a shallow copy representing that step.
- Step 0 reads `first_entry_file_name`.
- `storage.write(data)` writes to `operator_step + 1`.
- For `FileStorage(first_entry_file_name="input.jsonl", cache_path="cache", file_name_prefix="run", cache_type="jsonl")`:
  - step 0 reads `input.jsonl`.
  - the first operator writes `cache/run_step1.jsonl`.
  - the second operator reads step 1 and writes `cache/run_step2.jsonl`.

Use one `storage.step()` call per operator call in a pipeline `forward()`. Do not call `read()` or `write()` before stepping; the storage raises `ValueError` instructing you to call `storage.step()` first.

## Reading final outputs

To inspect the output of a two-operator file pipeline:

```python
reader = FileStorage("input.jsonl", cache_path="cache", file_name_prefix="run", cache_type="jsonl").reset()
for _ in range(3):  # step 0 input, step 1 first output, step 2 final output
    reader.step()
final_dataframe = reader.read(output_type="dataframe")
```

For a one-operator pipeline, step twice before reading the output.

## Storage selection matrix

| Storage | Offline safe | Formats | Main use | Important caveats |
| --- | --- | --- | --- | --- |
| `FileStorage` | Yes for local files | `json`, `jsonl`, `csv`, `parquet`, `pickle`, and observed `xlsx` support | Deterministic local pipeline input/cache. | Writes immediately. Step output filenames are `{file_name_prefix}_step{n}.{cache_type}`. |
| `LazyFileStorage` | Yes for local files | `json`, `jsonl`, `csv`, `parquet`, `pickle` | In-memory buffering with explicit or exit-triggered flush. | `write()` buffers and returns the future path; call `flush_step` or `flush_all` when you need files before process exit. |
| `DummyStorage` | Intended yes | Optional `json`, `jsonl`, `csv`, `parquet`, `pickle` cache | Wrapper internals and tests. | In `open-dataflow` 1.0.10, direct instantiation may fail because `get_keys_from_dataframe` is abstract. Prefer `FileStorage` for smoke tests. |
| `BatchedFileStorage` | Yes for local `jsonl`/`csv` | `jsonl`, `csv` | Batch slicing while using cache files. | Maintains `batch_size`, `batch_step`, and an in-memory dataframe buffer. Appends output batches to the same step file. |
| `StreamBatchedFileStorage` | Yes for local `jsonl`/`csv` | Optimized `jsonl`, `csv`; partial fallbacks for other formats | Streaming chunk reads for large files. | Header/key detection is cheap for CSV/JSONL; non-stream formats can fall back to full reads. |
| `MyScaleDBStorage` | No, requires DB | ClickHouse/MyScale table rows | Database-backed task input/output. | Requires live ClickHouse/MyScale connectivity and `pipeline_id`, `input_task_id`, `output_task_id`. |

## File formats

### JSON and JSONL

- JSON should be a record array readable by pandas.
- JSONL should contain one JSON object per line.
- JSONL is the best default for tiny skill examples and line-oriented cache inspection.

### CSV

- Headers define column names for compile-time validation.
- Batched CSV writes include a header for the first batch and append later batches without a header.

### Parquet

- Requires a Parquet engine available to pandas, usually `pyarrow`.
- `StreamBatchedFileStorage` can count rows from Parquet metadata but optimized chunk iteration is for JSONL/CSV.

### Pickle

- Uses pandas pickle support.
- Treat pickle inputs as trusted-only because pickle loading can execute code.

### XLSX

- `FileStorage` can read and write `.xlsx` when the cache type is set to `xlsx` and pandas has Excel support installed.
- For step-0 `.xlsx` input, instantiate `FileStorage(..., cache_type="xlsx")` so the storage knows to use Excel handling.
- XLSX is useful for manual inspection but JSONL/CSV are better for automated smoke tests.

## Remote source prefixes

`FileStorage` and `LazyFileStorage` recognize step-0 sources with these prefixes:

- `hf:dataset[:config][:split]` for Hugging Face datasets.
- `ms:dataset[:split]` for ModelScope datasets.

These are not offline-safe because they can require network access, credentials, or local dataset caches. Use local fixture files for verification unless the caller explicitly allows network use.

## Batched pipeline cache and resume files

`BatchedPipelineABC.forward(..., resume_from_last=True)` and `StreamBatchedPipelineABC.forward(..., resume_from_last=True)` record progress in:

```text
{cache_path}/{file_name_prefix}_last_success_step.txt
```

The file stores `step,batch_step`. If `resume_from_last=True` and the file exists, DataFlow resumes from that marker. If it does not exist, the run starts at step 0. Passing both `resume_step > 0` and `resume_from_last=True` raises `ValueError`.

Use a unique `file_name_prefix` per experiment if you do not want a previous resume marker or cache file to affect a new run.

## MyScaleDBStorage essentials

Constructor shape:

```python
MyScaleDBStorage(
    db_config={
        "host": "localhost",
        "port": 9000,
        "user": "default",
        "password": "",
        "database": "dataflow",
        "table": "dataflow_table",
    },
    pipeline_id="pipeline-a",
    input_task_id="task-in",
    output_task_id="task-out",
    parent_pipeline_id=None,
    page_size=10000,
    page_num=0,
)
```

Required instance parameters are `pipeline_id`, `input_task_id`, and `output_task_id`; missing values raise `ValueError`. Reads return the table `data` field expanded into columns when it contains dictionaries. Writes merge non-system columns into `data` and insert rows with `pipeline_id`, `task_id`, `raw_data_id`, `min_hashes`, `file_id`, `filename`, `parent_pipeline_id`, and `data`.
