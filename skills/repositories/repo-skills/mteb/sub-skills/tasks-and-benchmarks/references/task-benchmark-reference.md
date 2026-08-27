# Task and Benchmark Reference

## Public API Surface

- `mteb.get_task(task_name, languages=None, script=None, eval_splits=None, hf_subsets=None, exclusive_language_filter=False)` returns one initialized task object.
- `mteb.get_tasks(tasks=None, languages=None, script=None, domains=None, task_types=None, categories=None, exclude_superseded=True, eval_splits=None, exclusive_language_filter=False, modalities=None, exclusive_modality_filter=False, exclude_aggregate=False, exclude_private=True, exclude_beta=True)` returns `MTEBTasks`, a tuple-like collection with summary helpers.
- `mteb.filter_tasks(tasks, languages=None, script=None, domains=None, task_types=None, categories=None, modalities=None, exclusive_modality_filter=False, exclude_superseded=False, exclude_aggregate=False, exclude_private=False, exclude_beta=False)` filters an existing iterable of task objects or task classes.
- `mteb.get_benchmark(benchmark_name)` returns a predefined `Benchmark`; aliases such as shorter benchmark names can resolve to canonical names.
- `mteb.get_benchmarks(names=None, display_on_leaderboard=None)` returns a list of benchmark objects, optionally filtered to leaderboard-visible or non-leaderboard benchmarks.

## Task Discovery Patterns

```python
import mteb

# Named task selection; broad metadata filters are not used when tasks= is supplied.
tasks = mteb.get_tasks(tasks=["Banking77Classification"], eval_splits=["test"])

# Metadata discovery; criteria are combined as AND across fields.
retrieval = mteb.get_tasks(
    task_types=["Retrieval"],
    languages=["eng"],
    script=["Latn"],
    modalities=["text"],
)

# Single multilingual task with narrowed subsets/languages.
task = mteb.get_task(
    "AmazonReviewsClassification",
    languages=["eng", "fra"],
    eval_splits=["test"],
)
```

Expected signals:

- Returned task objects expose `task.metadata.name`, `task.metadata.type`, `task.metadata.languages`, `task.metadata.scripts`, `task.metadata.domains`, `task.metadata.modalities`, `task.eval_splits`, and often `task.hf_subsets`.
- `get_task(...)` raises `KeyError` with a close-match suggestion when the name is unknown.
- `get_tasks(tasks=[...], languages=[...])` skips named tasks whose subsets do not match the language filter and logs a warning.
- `get_tasks(exclude_beta=False)` can emit a warning that beta tasks are included.

## Benchmark Discovery Patterns

```python
import mteb

benchmark = mteb.get_benchmark("MTEB(eng, v2)")
print(benchmark.name, len(benchmark), benchmark.aliases)

leaderboard_benchmarks = mteb.get_benchmarks(display_on_leaderboard=True)
all_benchmark_names = [bench.name for bench in mteb.get_benchmarks()]
```

A `Benchmark` contains a sequence of task objects and metadata such as:

- `name`: canonical benchmark name.
- `aliases`: alternative accepted names.
- `tasks`: task sequence used by the benchmark.
- `description`, `reference`, `citation`, `contacts`: benchmark documentation metadata when available.
- `display_on_leaderboard`: computed boolean for leaderboard visibility.
- `language_view`: controls per-language leaderboard table availability.

## Filtering Benchmark Tasks

```python
import mteb

benchmark = mteb.get_benchmark("MTEB(eng, v2)")
retrieval_tasks = mteb.filter_tasks(
    benchmark,
    task_types=["Retrieval"],
    modalities=["text"],
    exclude_superseded=True,
    exclude_private=True,
    exclude_beta=True,
)
```

Use `filter_tasks(...)` rather than `get_tasks(tasks=benchmark_task_names, task_types=...)` when you want to preserve a benchmark subset and apply metadata filters. `filter_tasks` works on both task objects and task classes.

## Summary Helpers

`mteb.get_tasks(...)` returns `MTEBTasks`, which supports:

- `tasks.languages`: set of languages present in the returned tasks.
- `tasks.count_languages()`: `Counter` of language frequencies.
- `tasks.to_markdown(properties=(...), limit_n_entries=...)`: Markdown table summary.
- `tasks.to_dataframe(properties=(...))`: pandas DataFrame summary.
- `tasks.to_latex(properties=(...))`: LaTeX table summary.

Default summary properties include `name`, `type`, `languages`, `domains`, `license`, and `modalities`.

## Selection-to-Evaluation Handoff

After selection, route to `evaluation-workflows` for model execution. Valid handoff forms include:

```python
benchmark = mteb.get_benchmark("MTEB(eng, v2)")
# mteb.evaluate(model, tasks=benchmark)

selected_tasks = mteb.get_tasks(task_types=["Classification"], languages=["eng"])
# mteb.evaluate(model, tasks=selected_tasks)
```

Do not load datasets or call `mteb.evaluate(...)` merely to inspect availability. Use metadata inspection first, then evaluate only when the model, output/cache strategy, and runtime constraints are known.
