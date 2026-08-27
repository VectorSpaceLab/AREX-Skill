# Results Cache and Result Objects

## Cache Layout

MTEB result caches are directory trees managed by `mteb.ResultCache`.

Typical layout:

```text
<cache>/
  results/
    <model-name-as-path>/
      <revision-or-no_revision_available>/
        model_meta.json
        run_settings.jsonl
        <TaskName>.json
  remote/
    results/
      <model-name-as-path>/
        <revision>/
          model_meta.json
          <TaskName>.json
  leaderboard/
    benchmark_results.parquet
```

Important details:

- Local evaluation output usually lands under `results/`; downloaded public results land under `remote/results/`.
- Model names are path-normalized in folders, commonly replacing `/` with `__`.
- Each task result is one JSON file named like `STS12.json` or `Banking77Classification.v2.json`.
- `model_meta.json` is optional for ad hoc diagnostics but expected for reliable loading, model identity, publication, and submission.
- `run_settings.jsonl` may be written alongside result JSON files and records task/split/subset package versions and `encode_kwargs`.
- Experiment results may appear under `experiments/<experiment-name>/` below a revision folder.

## Core APIs

```python
import mteb

cache = mteb.ResultCache(cache_path="mteb-results-cache")
```

Useful `ResultCache` methods:

- `cache.load_task_result(task_name, model_name, model_revision=None, raise_if_not_found=False, prioritize_remote=False, experiment_name=None)` returns one `TaskResult` or `None`.
- `cache.load_results(models=None, tasks=None, require_model_meta=True, include_remote=True, validate_and_filter=False, only_main_score=False, load_experiments="match_kwargs", experiment_kwargs=None)` returns `BenchmarkResults`.
- `cache.get_cache_paths(models=None, tasks=None, require_model_meta=True, include_remote=True, load_experiments="no_experiments")` returns matching result JSON paths.
- `cache.get_models(tasks=None, require_model_meta=True, include_remote=True)` returns `(model_folder_name, revision)` pairs from cached result paths.
- `cache.get_task_names(models=None, require_model_meta=True, include_remote=True)` returns task names from cached result files.
- `cache.download_from_remote(download_latest=True, revision=None)` clones or updates the public results repository into `remote/`; it requires Git and network access.
- `cache.clear_cache()` clears the local cache tree; use only when the user explicitly wants deletion.
- `cache.save_to_cache(task_result, model_name, model_revision=None, encode_kwargs=None)` writes a `TaskResult`, plus metadata when `model_name` is a `ModelMeta`.

Top-level `mteb.load_results(...)` is deprecated; prefer `mteb.ResultCache(...).load_results(...)`.

## Loading Recipes

Load local and already-downloaded remote results for selected models and tasks:

```python
import mteb

cache = mteb.ResultCache(cache_path="mteb-results-cache")
tasks = mteb.get_tasks(tasks=["STS12"])
results = cache.load_results(
    models=["intfloat/multilingual-e5-large"],
    tasks=tasks,
    require_model_meta=True,
    include_remote=True,
)
print(results.model_names, results.task_names)
```

Download public results, then load legal retrieval tasks for English and French:

```python
import mteb

cache = mteb.ResultCache(cache_path="mteb-results-cache")
cache.download_from_remote()
tasks = mteb.get_tasks(task_types=["Retrieval"], languages=["eng", "fra"], domains=["Legal"])
results = cache.load_results(
    models=["GritLM/GritLM-7B", "intfloat/multilingual-e5-large"],
    tasks=tasks,
    include_remote=True,
)
df = results.to_dataframe(aggregation_level="task", format="long")
```

Load a benchmark and compute benchmark-specific summary rows:

```python
import mteb

benchmark = mteb.get_benchmark("MTEB(eng, v2)")
cache = mteb.ResultCache(cache_path="mteb-results-cache")
results = cache.load_results(tasks=benchmark, models=["intfloat/e5-small"])
summary = results.get_benchmark_result()
```

Use `require_model_meta=False` only to inspect legacy or incomplete folders:

```python
results = cache.load_results(require_model_meta=False, include_remote=False)
```

Expected signal: model names/revisions may be inferred from folder names rather than canonical metadata. Add valid `model_meta.json` before sharing or submitting.

## Result Objects

`TaskResult` represents one task JSON file. Common methods and properties:

- `TaskResult.from_disk(path)` and `task_result.to_disk(path)` read/write task JSON.
- `task_result.to_dict()` exposes serializable result content.
- `task_result.get_score(splits=None, languages=None, scripts=None, getter=None, aggregation=None)` returns an aggregate main score by default.
- `task_result.validate_and_filter_scores(task)` filters result splits/subsets/languages against current task metadata.
- `task_result.is_mergeable(other)` and `task_result.merge(other)` combine compatible task results, for example across subsets.
- `task_result.plot_evaluation_phases()` displays recorded timing phases when `evaluation_phases` exists.

`ModelResult` represents one model/revision and a list of `TaskResult` objects:

- Iterable and indexable: `model_result[0]` is a `TaskResult`.
- Properties include `model_name`, `model_revision`, `task_names`, `languages`, `domains`, `task_types`, and `modalities`.
- `model_result.select_tasks(tasks)` filters to task objects.
- `model_result.to_dataframe(aggregation_level="task", format="wide" | "long", include_model_revision=False)` builds a pandas dataframe.
- `model_result.to_disk(path)` and `ModelResult.from_disk(path)` round-trip full model-result containers.

`BenchmarkResults` represents multiple `ModelResult` objects:

- Iterable and indexable: `results[0]` is a `ModelResult`.
- Properties include `model_names`, `model_revisions`, `task_names`, `languages`, `domains`, and `task_types`.
- `results.select_models(names=[...], revisions=[...])` filters models; passing `ModelMeta` also pins the registered revision.
- `results.select_tasks(tasks)` filters all model results to selected task objects.
- `results.join_revisions()` chooses one revision per model, preferring the registered main revision when available.
- `results.to_dataframe(aggregation_level="subset" | "split" | "task" | "language", format="wide" | "long", include_model_revision=False)` builds comparison tables.
- `results.get_benchmark_result()` requires `results.benchmark` to be one benchmark and returns the benchmark summary table.
- `BenchmarkResults.save_leaderboard_cache(...)` and `BenchmarkResults.load_leaderboard_cache(...)` handle local leaderboard parquet caches.

## Dataframe Controls

Use `aggregation_level` intentionally:

- `"subset"`: one row per model/task/split/subset; most detailed.
- `"split"`: aggregate subsets within each split.
- `"task"`: aggregate to one score per model/task; best default for comparison tables.
- `"language"`: aggregate by language when working with multilingual results.

Use `format` intentionally:

- `"long"`: columns like `model_name`, `task_name`, `score`, and optionally `split`/`subset`; best for filtering, plotting, and joining metadata.
- `"wide"`: one score column per model; best for quick side-by-side inspection.

Use `include_model_revision=True` when multiple revisions are meaningful. If `False`, `BenchmarkResults.to_dataframe` joins revisions first.

## Validation Checklist

- `python -c "import mteb; print(mteb.__version__)"` succeeds in the active environment.
- `pip check` is clean, or dependency conflicts are understood before loading optional leaderboard/dataframe paths.
- Result JSON files are under `<cache>/results/<model-as-path>/<revision>/` or `<cache>/remote/results/<model-as-path>/<revision>/`.
- Task JSON files contain `task_name`, `scores`, `dataset_revision`, and `mteb_version` fields.
- Each score list contains dicts with `main_score`, `hf_subset`, and `languages` where available.
- Publication/submission candidates include `model_meta.json`; diagnostic-only folders can be loaded with `require_model_meta=False`.
- `cache.get_cache_paths(..., include_remote=False)` returns local files before submission; `include_remote=True` includes downloaded public results.
- `results.to_dataframe(format="long")` returns a non-empty dataframe with `model_name`, `task_name`, and `score` for meaningful comparisons.
