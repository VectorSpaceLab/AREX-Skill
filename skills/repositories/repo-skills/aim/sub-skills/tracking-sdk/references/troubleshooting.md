# Tracking SDK troubleshooting

Use this guide for Aim SDK instrumentation and local repository issues. CLI/server/storage operations and optional framework callbacks are handled by sibling sub-skills.

## Quick diagnostic checklist

1. Confirm the process imports the expected package:
   ```python
   import aim
   from aim import Repo, Run
   ```
2. Use an explicit repo path, not an accidental current working directory:
   ```python
   repo = Repo.from_path("./aim-repo", init=True)
   run = Run(repo=repo, system_tracking_interval=None, capture_terminal_logs=False)
   ```
3. Track one known scalar, close the run, then query with progress disabled.
4. If using temporary directories, close all `Run` and `Repo` objects before deleting the directory.
5. If opening for reads, use `Run(..., read_only=True)` or `repo.get_run(hash)`, not `Repo(read_only=True)`.

`scripts/aim_sdk_smoke.py` implements this checklist in a safe, repeatable way.

## Metrics do not appear

Common causes and fixes:

### The run was not closed before querying or cleanup

Aim flushes and finalizes resources during `run.close()`. Always close the run before querying from a fresh process or deleting temporary storage.

```python
run = Run(repo=repo, system_tracking_interval=None, capture_terminal_logs=False)
try:
    run.track(1.0, name="loss")
finally:
    run.close()
```

### The code wrote to a different repository

`Run()` with no `repo` uses the default repo searched from the current working directory. Agents and tests may run from unexpected directories. Prefer:

```python
repo = Repo.from_path(str(repo_dir), init=True)
run = Run(repo=repo, ...)
```

### Fresh SDK-only writes are not indexed yet

Repository query methods read indexed metadata. If a short script writes a run, closes it, and immediately queries from the same process, query results can be stale until the run is indexed. For bounded validation without starting UI/server components:

```python
from aim.sdk.index_manager import RepoIndexManager

run.close()
RepoIndexManager.get_index_manager(repo).index(run_hash)
```

Then query with `QueryReportMode.DISABLED`.

### The query filters out the data

Start broad, then narrow:

```python
all_metrics = list(repo.query_metrics(report_mode=QueryReportMode.DISABLED))
print([(m.name, m.context.to_dict(), m.run.hash) for m in all_metrics])
for metric in all_metrics:
    metric.run.close()
```

Then apply the intended expression. Remember that empty queries exclude archived runs unless `run.archived` appears in the query.

### The context does not match

A sequence identity includes context. These are different sequences:

```python
run.track(0.5, name="loss", context={"subset": "val"})
run.track(0.5, name="loss", context={"subset": "validation"})
```

Use the exact context in exact retrieval:

```python
from aim.storage.context import Context

run.get_metric("loss", context=Context({"subset": "val"}))
```

`run.track(...)` accepts plain dictionaries for contexts, but exact getter methods in this Aim version expect Aim's hashable `Context` wrapper.

or query the context explicitly:

```python
"metric.name == 'loss' and metric.context.subset == 'val'"
```

### The run is archived

Default queries include `run.archived == False`. Query archived runs explicitly:

```python
repo.query_runs("run.archived == True", report_mode=QueryReportMode.DISABLED)
```

## Temporary-directory cleanup failures

Symptom examples:

- Missing or partially written metric data in a smoke test.
- Cleanup errors from files under the Aim repository.
- RocksDB-backed resources still open when the directory is removed.

Safe pattern:

```python
repo_dir = Path(tempfile.mkdtemp(prefix="aim-sdk-"))
repo = None
run = None
try:
    repo = Repo.from_path(str(repo_dir), init=True)
    run = Run(repo=repo, system_tracking_interval=None, capture_terminal_logs=False)
    run.track(1.0, name="ok")
finally:
    if run is not None:
        run.close()
    if repo is not None:
        repo.close()
    gc.collect()
    time.sleep(0.1)
    shutil.rmtree(repo_dir, ignore_errors=True)
```

Avoid `with tempfile.TemporaryDirectory() as repo_dir:` around live Aim `Run`/`Repo` objects unless cleanup occurs after explicit close operations.

## Read-only repository misuse

In the verified Aim version, this raises `NotImplementedError`:

```python
Repo("./aim-repo", read_only=True)
Repo.from_path("./aim-repo", read_only=True)
```

Use read-only runs instead, after the run has been closed and indexed if it was just written:

```python
repo = Repo.from_path("./aim-repo")
read_run = Run(run_hash=run_hash, repo=repo, read_only=True)
try:
    params = read_run.get("hparams", default=None)
finally:
    try:
        read_run.close()
    except AttributeError:
        # Some Aim 3.29.x read-only Run objects can raise while closing after their no-op finalizer ran.
        pass
    repo.close()
```

or:

```python
read_run = repo.get_run(run_hash)
```

## Type compatibility errors

Typical error:

```text
Cannot log value '[1]' on sequence 'numbers'. Incompatible data types.
```

Cause: a fixed `(run, name, context)` sequence already has an inferred dtype. Aim allows compatible numeric scalar transitions such as int/float, but not switching a metric sequence to a list/object sequence.

Fixes:

- Use a new sequence name for a new data type.
- Use a different context if the semantic stream is distinct.
- Convert multi-value arrays to supported objects or summarize them as scalar metrics.

Examples:

```python
# OK: separate contexts
run.track(1.0, name="score", context={"type": "float"})
run.track([1.0], name="score", context={"type": "list"})

# OK: separate names
run.track(1.0, name="score")
run.track([1.0], name="score_vector")
```

## `name` argument errors

When tracking a dictionary, `name` must be omitted:

```python
run.track({"loss": 0.2, "accuracy": 0.9}, step=1, context={"subset": "val"})
```

When tracking a single value, `name` is required:

```python
run.track(0.2, name="loss", step=1)
```

## NumPy scalar and array issues

Accepted as metrics:

- `np.float64(1.0)`, `np.float32(1.0)`
- one-item arrays such as `np.array([1.0])` and `np.array([[[1.0]]])`

Rejected as scalar metrics:

- multi-item arrays such as `np.array([1.0, 2.0])`

Fixes:

- Reduce to scalar: `float(array.mean())`.
- Track as `Image`, `Distribution`, or another Aim object when the array represents media or a distribution.

## Query returns no rows or raises syntax errors

Checklist:

- Use `and`/`or`, not `&&`/`||`.
- Use the correct sequence variable for the query method: `metric` for metrics, `images` for images, `texts` for texts, etc.
- Start with an empty query to list available names/contexts.
- Disable progress bars in scripts: `report_mode=QueryReportMode.DISABLED`.
- Remember archived runs are excluded unless explicitly queried.

Invalid:

```python
"run.hash == 'x' && metric.name == 'loss'"
```

Valid:

```python
"run.hash == 'x' and metric.name == 'loss'"
```

## Dataframe is `None` or pandas fails

- `SequenceCollection.dataframe()` returns `None` for empty collections.
- Dataframe helpers require pandas to be importable.
- Query broadly and assert the collection is non-empty before calling dataframe-specific logic.

```python
collection = repo.query_metrics("metric.name == 'loss'", report_mode=QueryReportMode.DISABLED)
metrics = list(collection)
if not metrics:
    raise AssertionError("No loss metrics found")
for metric in metrics:
    df = metric.dataframe(include_name=True, include_context=True)
    metric.run.close()
```

## Image/Text/Distribution/Audio/Figure constructor issues

- `Image`: file path must exist; NumPy arrays must be 2-D or 3-D; unsupported object types raise `TypeError`.
- `Text`: input must be `str`.
- `Distribution`: pass either `samples` or `hist` with `bin_range`, not both; at least one is required.
- `Audio`: pass `format='mp3'`, `'wav'`, or `'flac'`; non-bytes streams and missing files fail.
- `Figure`: Plotly figures are the safest. Matplotlib conversion requires Plotly and may not preserve every visual detail; use `Image(fig)` as a static fallback.

## Artifact URI warnings

`run.set_artifacts_uri()` expects a URI scheme:

```python
run.set_artifacts_uri(Path("./artifacts").resolve().as_uri())
```

A plain path can emit a warning. Remote/cloud artifact uploads require storage credentials and should not be assumed in a local smoke test.

## System tracking and terminal logs create extra sequences

Default `Run()` may start resource tracking and terminal capture. If a test expects only user metrics, use:

```python
Run(system_tracking_interval=None, log_system_params=False, capture_terminal_logs=False)
```

If the user needs resource metrics or logs, keep the defaults or set the interval explicitly, then account for extra sequences in queries.

## Safe smoke validation

Run the bundled script after installing Aim:

```shell
python scripts/aim_sdk_smoke.py --keep-repo
```

or validate a chosen repository directory:

```shell
python scripts/aim_sdk_smoke.py --repo-dir ./aim-smoke-repo
```

Expected signal:

- It prints `ASSERT PASS` lines for imports, repo creation, run tracking, metric queries, image queries, read-only run access, query syntax behavior, and explicit close/cleanup.
- It exits with status 0.
- If Plotly or pandas is unavailable, it may skip optional figure/dataframe checks while still validating the core SDK workflow.
