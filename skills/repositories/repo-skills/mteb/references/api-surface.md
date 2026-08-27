# Shared MTEB API Surface

This reference lists the top-level APIs and CLI commands shared across MTEB sub-skills. Use the focused sub-skills for workflow depth and troubleshooting.

## Top-Level Imports

```python
import mteb
```

Frequently used exports:

- `mteb.evaluate(model, tasks, ...)`: run evaluations and return a `ModelResult`.
- `mteb.get_tasks(...)`, `mteb.get_task(...)`: select task objects.
- `mteb.filter_tasks(...)`: filter an existing task iterable by metadata.
- `mteb.get_benchmark(...)`, `mteb.get_benchmarks(...)`: select predefined benchmark objects.
- `mteb.get_model(...)`, `mteb.get_model_meta(...)`, `mteb.get_model_metas(...)`: load models or inspect model metadata.
- `mteb.ResultCache(cache_path=...)`: read/write local and remote result caches.
- `mteb.load_results(...)`: load public or local results into `BenchmarkResults`.
- `mteb.TaskMetadata`, `mteb.AbsTask`, and task subclasses: implement or inspect tasks.
- `mteb.Benchmark`, `mteb.BenchmarkResults`, and `mteb.TaskResult`: benchmark and result containers.

## Verified Signatures

```python
mteb.evaluate(
    model,
    tasks,
    *,
    co2_tracker=None,
    raise_error=True,
    encode_kwargs=None,
    cache=mteb.ResultCache(...),
    overwrite_strategy="only-missing",
    prediction_folder=None,
    show_progress_bar=True,
    public_only=None,
    num_proc=None,
    timer=None,
)
```

```python
mteb.get_tasks(
    tasks=None,
    languages=None,
    script=None,
    domains=None,
    task_types=None,
    categories=None,
    exclude_superseded=True,
    eval_splits=None,
    exclusive_language_filter=False,
    modalities=None,
    exclusive_modality_filter=False,
    exclude_aggregate=False,
    exclude_private=True,
    *,
    exclude_beta=True,
)
```

```python
mteb.get_model(model_name, revision=None, device=None, *, embed_dim=None, **kwargs)
```

```python
mteb.load_results(
    results_repo="https://github.com/embeddings-benchmark/results",
    download_latest=True,
    models=None,
    tasks=None,
    validate_and_filter=True,
    require_model_meta=True,
    only_main_score=False,
)
```

## CLI Commands

Validate the installed command surface before scripting:

```bash
mteb --help
mteb run --help
mteb available-tasks --help
mteb available-benchmarks --help
mteb create-model-results --help
mteb leaderboard --help
```

Current command families:

- `mteb run`: load a model, select tasks or benchmarks, run evaluation, and write result cache files.
- `mteb available-tasks`: list installed tasks with a subset of task filters.
- `mteb available-benchmarks`: list benchmark definitions.
- `mteb create-model-results`: create or update model-card result metadata from cached results.
- `mteb leaderboard`: launch a local leaderboard app; requires leaderboard optional dependencies.

If older examples mention `create-meta`, treat it as the same model-card metadata workflow and verify the actual installed subcommand with `mteb --help`.

## Safe First Checks

```bash
python -c "import mteb; print(mteb.__version__)"
python -m pip check
mteb --help
```

These checks do not run benchmarks, download datasets, or load remote models. They only prove the package and command entry point are importable enough for deeper workflow work.
