# Evaluation Recipes

## Minimal Python Evaluation

Use this when the user already chose a model and a small public task.

```python
import mteb

model = mteb.get_model("sentence-transformers/all-MiniLM-L6-v2")
tasks = mteb.get_tasks(tasks=["Banking77Classification.v2"])
results = mteb.evaluate(
    model,
    tasks=tasks,
    cache=mteb.ResultCache(cache_path="mteb-results-cache"),
    overwrite_strategy="only-missing",
    co2_tracker=False,
)
print(results.task_results[0].task_name)
print(results.task_results[0].get_score())
```

Expected signals: one successful `TaskResult`, a non-empty model name/revision when metadata is available, and a cache entry under the configured cache path.

## Evaluate a Benchmark or Task List

```python
import mteb

model = mteb.get_model("mteb/baseline-random-encoder")
tasks = mteb.get_tasks(
    tasks=["Banking77Classification.v2", "STS12"],
    exclude_private=True,
    exclude_beta=True,
    exclude_superseded=True,
)
results = mteb.evaluate(
    model,
    tasks=tasks,
    cache=mteb.ResultCache(cache_path="mteb-results-cache"),
    raise_error=False,
    co2_tracker=False,
)

print("ok", [r.task_name for r in results.task_results])
print("failed", [(e.task_name, e.exception) for e in results.exceptions])
```

Use `raise_error=False` for long multi-task runs so one bad task does not discard all successful results. Use `raise_error=True` when narrowing a single failure.

## Resume a Run With Only Missing Work

```python
cache = mteb.ResultCache(cache_path="mteb-results-cache")
results = mteb.evaluate(
    model,
    tasks=tasks,
    cache=cache,
    overwrite_strategy="only-missing",
    co2_tracker=False,
)
```

Expected behavior: if a compatible result exists, MTEB skips completed work; if an earlier run cached only some splits/subsets, MTEB evaluates the missing pieces and merges compatible results.

## Load Cached Results Without Evaluating

```python
cache = mteb.ResultCache(cache_path="mteb-results-cache")
results = mteb.evaluate(
    model,
    tasks=tasks,
    cache=cache,
    overwrite_strategy="only-cache",
    co2_tracker=False,
)
```

Expected behavior: cached complete results load. If no compatible cache entry exists, MTEB raises `ValueError` mentioning `overwrite_strategy is set to 'only-cache'`.

Use this for CI checks or result inspection where downloads and model inference must not occur.

## Avoid Overwriting Existing Results

```python
results = mteb.evaluate(
    model,
    tasks=tasks,
    cache=mteb.ResultCache(cache_path="mteb-results-cache"),
    overwrite_strategy="never",
    co2_tracker=False,
)
```

Expected behavior: complete cached results are reused. If the result is absent, the task can run and write a new cache entry. If an incomplete normal-task cache entry exists, MTEB raises rather than silently changing it.

## Force a Clean Re-Evaluation

```python
results = mteb.evaluate(
    model,
    tasks=tasks,
    cache=mteb.ResultCache(cache_path="mteb-results-cache"),
    overwrite_strategy="always",
    encode_kwargs={"batch_size": 16},
    co2_tracker=False,
)
```

Use this when the model implementation, preprocessing, task revision, or encode settings changed and cached scores should not be trusted.

## Pass Encoder Arguments

```python
results = mteb.evaluate(
    model,
    tasks=tasks,
    encode_kwargs={
        "batch_size": 64,
        "show_progress_bar": False,
    },
    cache=mteb.ResultCache(cache_path="mteb-results-cache"),
    co2_tracker=False,
)
```

MTEB forwards `encode_kwargs` to task encoders. If `batch_size` is omitted, MTEB sets it to `32`. Some wrapped models also record meaningful encode settings in experiment metadata, so keep stable settings for reproducible cache comparisons.

## Save Predictions

```python
results = mteb.evaluate(
    model,
    tasks=tasks,
    prediction_folder="predictions",
    cache=mteb.ResultCache(cache_path="mteb-results-cache"),
    co2_tracker=False,
)
```

Expected output for supported task types: files like `predictions/{task_name}_predictions.json`, containing model identity plus task-specific predictions or rankings. Not every task type has equally useful prediction output; verify the file exists before building downstream logic.

## Track CO2 Emissions

```python
results = mteb.evaluate(
    model,
    tasks=tasks,
    co2_tracker=True,
    cache=mteb.ResultCache(cache_path="mteb-results-cache"),
)
```

Prerequisite: install the optional `codecarbon` extra, commonly as `mteb[codecarbon]`. Without it, `co2_tracker=True` raises an import error. Leaving `co2_tracker=None` lets MTEB track only when the optional dependency is importable.

## Handle Private Dataset Access

For public-only runs, filter tasks before evaluation:

```python
tasks = mteb.get_tasks(
    domains=["News"],
    exclude_private=True,
    exclude_beta=True,
    exclude_superseded=True,
)
results = mteb.evaluate(model, tasks=tasks, public_only=True)
```

For a known private task where the user has access:

```python
results = mteb.evaluate(
    model,
    tasks=private_tasks,
    public_only=False,
    raise_error=True,
)
```

Expected behavior: `public_only=False` raises dataset access errors instead of treating private misses as warnings, which is useful for fixing Hugging Face authentication or permissions.

## Speed and Stability Knobs

```python
results = mteb.evaluate(
    model,
    tasks=tasks,
    num_proc=4,
    encode_kwargs={"batch_size": 128},
    show_progress_bar=False,
    cache=mteb.ResultCache(cache_path="mteb-results-cache"),
)
```

- Increase `batch_size` until the model backend reaches memory limits, then back off.
- Increase `num_proc` for dataset loading/transforms when CPU and I/O allow it.
- Set `num_proc=1` or `None` if multiprocessing causes deadlocks, serialization errors, or dataset transform failures.
- Install optional extras for required modalities or download acceleration, such as image dependencies, `codecarbon`, or `xet`, only when the chosen task/model requires them.

## CLI Equivalent Pointer

The common CLI equivalent is:

```bash
mteb run -m sentence-transformers/all-MiniLM-L6-v2 -t Banking77Classification.v2 --output-folder results
```

Use the `cli-and-automation` sub-skill for exact CLI flags and automation patterns; keep this sub-skill focused on the Python API.
