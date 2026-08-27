# Cross-cutting troubleshooting

## Import and dependency failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'psutil'` when importing CLI/model code | The SDV/RDT categorical transformer path imports `psutil`, but this dependency may not be declared by the package metadata in the inspected version. | Install `psutil` in the active environment, then rerun `python -m pip check` and `sdgx --help`. |
| `No module named sdgx` | Wrong Python environment or package not installed. | Run `python -m pip install sdgx` or install the checkout, then verify `python -c 'import sdgx; print(sdgx.__version__)'`. |
| Import succeeds only inside a checkout | Current directory is masking a broken install. | Run import checks from another directory and use `python -I` when possible. |
| `pip check` reports resolver conflicts after installing `table-evaluator` or test extras | Transitive dependencies are broad and may pin older pytest/Sphinx/pandas versions. | Use a fresh environment for SDGX, avoid test/docs extras unless needed, and install only the workflow's required extras. |

## Metadata and data processing failures

- `MetadataInvalidError` usually means a primary key is not in `column_list`, a column lacks an inferred type, a type set contains an unknown column, or categorical encoder/threshold keys are invalid. Use the data-preparation script to inspect metadata before fitting.
- `DatetimeFormatter` removes datetime columns that lack a `datetime_format`. If the sampled table is missing date columns, set `metadata.datetime_format` before fitting.
- `SpecificCombinationTransformer` only acts when `metadata.get("specific_combinations")` has groups such as `{("education", "educational-num")}`. Use this when automatic fixed-combination detection is too weak or too broad.
- `FixedCombinationInspector` may infer broad numeric correlations on tiny data. Validate fixed combinations before using them for production sampling.
- `GeneratorConnector` must be paired with a real cache; `NoCache` raises `DataLoaderInitError` because generators cannot provide random access.

## Cache and filesystem failures

- `DiskCache` writes parquet blocks, so `pyarrow` must be installed.
- `DiskCache.clear_invalid_cache()` clears all cache files by design in this version; use a workflow-specific `cacher_kwargs={"cache_dir": ...}` when you need isolation.
- `NDArrayLoader` writes column-wise `.npy` files under `SDG_NDARRAY_CACHE_ROOT` or a default `.ndarry_cache` directory. Clean caches after large experiments.

## CLI failures

- CLI wrapper exits with a nonzero code and logs exceptions. Add `--json_output true` to receive a structured JSON message for success/failure.
- Many CLI options that accept nested settings expect JSON strings, for example `--model_kwargs '{"epochs":1,"device":"cpu"}'` and `--data_connector_kwargs '{"path":"input.csv"}'`.
- Click boolean options are declared as `type=bool`; pass `true`/`false` explicitly rather than relying on flag presence.

## CUDA and model failures

- CTGAN defaults to CUDA when PyTorch sees a GPU. For portable smoke tests and CPU-only hosts, pass `device="cpu"` and small `epochs`/`batch_size` values.
- If CUDA is visible but PyTorch says `torch.cuda.is_available() == False`, the installed torch wheel, driver, or container GPU passthrough is mismatched. Fix the environment before claiming CUDA coverage.
- `batch_size` for CTGAN must be even because the constructor asserts `batch_size % 2 == 0`.

## LLM and credential failures

- `SingleTableGPTModel.check()` raises `InitializationError` when `openai_API_key` is empty.
- Set `OPENAI_KEY` and optionally `OPENAI_URL`, or call `set_openAI_settings(API_url, API_key)`. Redact keys in logs and reports.
- Do not send sensitive raw rows to an external LLM unless the user explicitly permits it; use metadata-only generation when appropriate.
