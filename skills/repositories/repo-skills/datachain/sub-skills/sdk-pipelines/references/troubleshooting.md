# SDK Pipeline Troubleshooting

Use this when DataChain SDK code imports but a pipeline fails, recomputes
unexpectedly, writes the wrong shape, or cannot access storage/model backends.

## Install and Import

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: datachain` | Active Python environment lacks DataChain. | Install with `pip install datachain` or run in the environment where the project declared DataChain. |
| `ImportError: Missing dependencies for torch` when importing `datachain.torch` | Optional `torch` extra is not installed. | Install `pip install 'datachain[torch]'` or avoid `to_pytorch` / `datachain.torch` helpers. |
| Optional HF/video/vector/audio/Postgres/Zarr workflow fails at import | Optional dependency group not installed. | Install the narrow extra for the selected workflow only; do not install all extras by default. |
| `datachain.__version__` is missing or unexpected | Editable/dev install, non-package execution, or wrong environment. | Run `python -c "import datachain, importlib.metadata as m; print(m.version('datachain'))"` in the intended environment. |

## UDF Output Type Errors

DataChain must know the output type for every `map`, `gen`, or Python `agg`.

Common fixes:

```python
# Good: annotation is enough.
def score(text: str) -> float:
    return 0.5

chain.map(score=score)

# Good: non-str lambda uses output=.
chain.map(score=lambda text: 0.5, params=["text"], output={"score": float})
```

Avoid `from __future__ import annotations` in files that define DataChain UDF
return types or `DataModel` classes consumed by DataChain. It can turn types
into strings and break schema resolution.

## `map` vs `mutate`

| Symptom | Cause | Recovery |
| --- | --- | --- |
| Passing a lambda to `mutate` fails | `mutate` accepts SQL-style expressions, not Python callables. | Use `map` for Python, or rewrite with `dc.C` and `dc.func`. |
| Pipeline downloads files only to derive path metadata | UDF parameter receives `file` instead of `file.path`. | Bind metadata fields with `params=["file.path"]`, `params=["file.size"]`, etc. |
| Simple group/filter is slow after `to_pandas()` | Work was pulled into Python. | Use native `filter`, `group_by`, `sum`, `avg`, `order_by`, and `select`. |

## Storage Access

- Bucket/prefix URIs should end in `/`: `s3://bucket/prefix/`.
- Use `anon=True` for public buckets when you know anonymous access is intended.
- `anon` on an upstream `read_storage` does not automatically become credentials
  for later saved-dataset file reads in a new process. Use a session with
  `client_config={"anon": True}` when downstream UDFs reopen public files.
- For private buckets, confirm normal cloud credential locations or pass an
  appropriate `client_config`. Do not print secrets.
- For a single file, use `dc.File.at(...)`; for directories or globs, use
  `read_storage(...)` so lineage is tracked.

## Save, Persist, and Reuse

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Expensive inference reruns for each downstream result | Shared upstream chain was not materialized. | Save or persist the expensive stage before branching. |
| Later questions cannot reuse model outputs | Pipeline ended in `show`, `to_list`, or a file dump instead of `.save()`. | Save UDF/model/LLM outputs as a named dataset first; export from the saved result if needed. |
| `.persist()` output is not listed for teammates | `persist()` creates an anonymous cache, not a named dataset. | Use `.save("name")` for collaboration and knowledge-base use. |

## Checkpoints

Checkpoints are tied to script path and chain hash.

- Normal script execution and Studio `job run` can reuse checkpoints.
- Interactive sessions and `python -m module` do not use checkpoints.
- Changing filter conditions, source versions, operation order, output type, or
  successful UDF code changes invalidates the relevant stage.
- Fixing a failing UDF without changing output type can resume from partial
  results.
- Set `DATACHAIN_IGNORE_CHECKPOINTS=1` only when a fresh run is required.

## Delta and Retry

- `delta=True` processes only new or changed records relative to previous source
  versions.
- `delta_retry` reprocesses rows with errors or missing output rows.
- `delta_on` identifies records; `delta_compare` identifies modifications.
- Delta is restricted with `merge`, `union`, `subtract`, `diff`, `file_diff`,
  `distinct`, `agg`, and `group_by` because those operations normally need the
  full dataset. Use `delta_unsafe=True` only after verifying consistency.

## Exports and File Placement

- Flat exports (`to_csv`, `to_json`, `to_parquet`) flatten nested model leaves
  into dotted column names.
- `to_storage(..., placement="filename")` may collide on duplicate filenames.
- Use `placement="filepath"` to preserve relative source paths and `"etag"` for
  digest-based uniqueness when storage exposes ETags.
- `to_pandas()` is bounded by memory; use it only after filtering or limiting.

## LLM and Provider Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Provider auth error | Missing API key, cloud IAM, or wrong provider prefix. | Configure credentials outside code and confirm `.settings(llm="provider/model")`. |
| Model sees a path string instead of file content | A string column was passed to `llm.*`. | Read storage as `type="text"`/`"image"` and pass the file column, or pass the actual text column. |
| Structured output parse error | Model lacks structured-output support or schema is too complex. | Simplify the Pydantic schema, choose a structured-output capable model, or handle row-level errors. |
| Token usage columns missing | `include_usage=True` was used without naming both outputs. | Use `.map(llm.complete(..., include_usage=True), output={"res": str, "usage": dc.llm.Usage})`. |

## Local Smoke Checks

- `python scripts/local_io_smoke.py` verifies a local, temporary DataChain
  read/save/export path.
- `python scripts/delta_retry_smoke.py --explain` prints the delta/retry contract;
  `python scripts/delta_retry_smoke.py` runs a small local demonstration.
