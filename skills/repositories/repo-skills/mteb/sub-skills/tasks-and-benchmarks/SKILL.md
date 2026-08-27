---
name: tasks-and-benchmarks
description: "Discover, filter, inspect, and reason about MTEB tasks and
  predefined benchmarks before evaluation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MTEB Tasks and Benchmarks

Use this sub-skill when the user needs to choose MTEB tasks or benchmarks, inspect task metadata, filter by language/script/domain/task type/category/modality, understand beta/private/superseded defaults, or compare benchmark task lists.

## Route First

- For running selected tasks or benchmarks with a model, use `../evaluation-workflows/SKILL.md` after selection is complete.
- For shell workflows around `mteb available-tasks` or `mteb available-benchmarks`, use `../cli-and-automation/SKILL.md`.
- For implementing or registering new tasks, use `../contributing-to-mteb/SKILL.md`.

## Core Workflows

- Select named tasks with `mteb.get_tasks(tasks=[...])` or one task with `mteb.get_task(name, languages=..., script=..., eval_splits=..., hf_subsets=...)`; named-task selection ignores broad `domains`, `task_types`, and `categories` filters, so apply `mteb.filter_tasks(...)` to a returned list if both name and metadata filtering are required.
- Discover tasks with `mteb.get_tasks(languages=..., script=..., domains=..., task_types=..., categories=..., modalities=..., eval_splits=...)`; filters are combined as an AND operation, with OR semantics inside each list unless an exclusive flag is documented.
- Select benchmarks with `mteb.get_benchmark("MTEB(eng, v2)")` or enumerate them with `mteb.get_benchmarks(names=..., display_on_leaderboard=...)`; a `Benchmark` is iterable and can be passed as `tasks=` to evaluation.
- Filter benchmark tasks with `mteb.filter_tasks(benchmark, task_types=[...], languages=[...], modalities=[...])`, then pass the filtered list to evaluation.
- Inspect selections safely with `scripts/inspect_task_selection.py`; it imports MTEB and prints task/benchmark summaries without downloading datasets or running models.

## References

- `references/task-benchmark-reference.md` - API patterns for task and benchmark discovery, selection, and benchmark filtering.
- `references/metadata-and-filters.md` - metadata fields, filter semantics, language/script distinctions, and default exclusion behavior.
- `references/troubleshooting.md` - diagnosis for import issues, optional dependencies, private/beta/superseded surprises, task-name typos, and CLI/API misuse.

## Quick Validation

- Confirm package import with `python -c "import mteb; print(mteb.__version__)"`.
- Preview a task filter with `python scripts/inspect_task_selection.py --task-types Retrieval --languages eng --format markdown --limit 20`.
- Preview a benchmark with `python scripts/inspect_task_selection.py --benchmark "MTEB(eng, v2)" --task-types Retrieval --format json --limit 10`.
- If selection looks correct, hand the task objects, task names, or benchmark to `evaluation-workflows` for actual `mteb.evaluate(...)` usage.
