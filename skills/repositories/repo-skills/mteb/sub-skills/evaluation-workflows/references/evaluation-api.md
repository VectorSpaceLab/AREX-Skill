# Evaluation API Reference

## Entry Point

Use `mteb.evaluate(model, tasks, *, co2_tracker=None, raise_error=True, encode_kwargs=None, cache=ResultCache(...), overwrite_strategy="only-missing", prediction_folder=None, show_progress_bar=True, public_only=None, num_proc=None, timer=None)` to run one task, a list of tasks, an aggregate task, or a benchmark-like task collection.

Inputs normally come from:

```python
import mteb

model = mteb.get_model("sentence-transformers/all-MiniLM-L6-v2")
tasks = mteb.get_tasks(tasks=["Banking77Classification.v2"])
results = mteb.evaluate(model, tasks=tasks)
```

For model-loading details, use the `models-and-encoders` sub-skill. For task filtering, use the `tasks-and-benchmarks` sub-skill.

## Parameters That Change Evaluation Behavior

| Parameter | Use | Expected signal |
| --- | --- | --- |
| `model` | `ModelMeta`, MTEB model wrapper, SentenceTransformer, CrossEncoder, or custom encoder with MTEB-compatible methods. | Returned `ModelResult.model_name` and `model_revision` reflect model metadata when available. |
| `tasks` | Single `AbsTask`, iterable of tasks, benchmark task list, or aggregate task. | One `TaskResult` per task, unless task failures are collected or skipped. |
| `cache` | `mteb.ResultCache(cache_path=...)`, default cache, or `None` to disable result caching. | Cache writes JSON results under model/revision/task paths and can reload them on later runs. |
| `overwrite_strategy` | One of `"always"`, `"never"`, `"only-missing"`, `"only-cache"`. | Controls rerun, resume, skip, or cache-only behavior. |
| `encode_kwargs` | Extra keyword arguments passed to task encoders, such as `batch_size`, `precision`, or backend-specific controls. | Encoders receive the kwargs; `batch_size` defaults to `32` if not supplied. |
| `prediction_folder` | Folder where tasks that support prediction export write `{task_name}_predictions.json`. | Prediction files appear for supported task types after evaluation. |
| `co2_tracker` | `True`, `False`, or `None`; `True` requires `mteb[codecarbon]`. | `TaskResult.kg_co2_emissions` is populated when tracking succeeds. |
| `raise_error` | `True` raises task exceptions; `False` records failures in `ModelResult.exceptions`. | Batch runs can finish with successful `task_results` plus recorded exceptions. |
| `public_only` | `None`, `True`, or `False` for private dataset behavior. | Private dataset misses can warn/skip with default behavior, or raise when forced with `False`. |
| `num_proc` | Worker count for dataset loading, transforms, prediction post-processing, or task-specific multiprocessing. | Faster loading/transforms when supported; reduce on multiprocessing errors. |
| `show_progress_bar` | Toggles outer progress and can set `encode_kwargs["show_progress_bar"] = False` when no kwargs are supplied. | Cleaner logs in CI or scripts. |

## Cache and Overwrite Semantics

- `"only-missing"` is the default. It loads compatible existing cache entries and evaluates missing splits/subsets only.
- `"only-cache"` never evaluates a normal missing task. It raises `ValueError` when no compatible cached result exists or when required splits/subsets are missing.
- `"never"` uses a complete cached result without overwriting it. If no result exists, it can run and write the result; if an incomplete normal-task result exists, it raises instead of silently modifying it.
- `"always"` reruns and overwrites the task result.
- MTEB writes intermediate cache entries after subset batches, so a crash in a later subset can leave a reusable partial cache for `"only-missing"`.
- Aggregate tasks can combine cached subtask results under cache-only behavior, then cache the aggregate result.

## Result Objects

`mteb.evaluate` returns a `ModelResult`:

```python
results = mteb.evaluate(model, tasks, cache=cache, co2_tracker=False)
print(results.model_name)
print(results.model_revision)
print(len(results.task_results))
print(results.exceptions)
```

Each successful item in `results.task_results` is a task-level result with fields such as `task_name`, `eval_splits`, scores, `evaluation_time`, optional `kg_co2_emissions`, and `get_score()`.

## Private and Public Dataset Behavior

MTEB tasks may refer to public or private Hugging Face datasets. If a private task's dataset cannot be loaded and `public_only` is left as `None`, MTEB warns that the dataset was not found and returns a task error rather than producing a task result. If `public_only=False`, dataset access failures are raised so the user can fix authentication or permissions.

Use task filtering before evaluation when the user wants a public-only run:

```python
tasks = mteb.get_tasks(
    tasks=["SomeTask"],
    exclude_private=True,
    exclude_beta=True,
    exclude_superseded=True,
)
```

## Validation Steps

1. Check API availability:

   ```python
   import inspect, mteb
   print(inspect.signature(mteb.evaluate))
   ```

2. Run a tiny safe smoke check with the bundled script:

   ```bash
   python scripts/smoke_evaluate_with_mock.py
   ```

3. For a real task, start with one small public task and `cache=mteb.ResultCache(cache_path="mteb-results-cache")`.
4. Re-run with `overwrite_strategy="only-cache"` only after the first run has successfully populated cache.
5. Confirm `len(results.task_results)` and inspect `results.exceptions` when `raise_error=False`.
