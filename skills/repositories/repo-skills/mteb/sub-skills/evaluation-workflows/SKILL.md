---
name: evaluation-workflows
description: "Run MTEB evaluations from Python, configure
  cache/overwrite/prediction/CO2/parallelism options, and troubleshoot
  evaluation failures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Evaluation Workflows

Use this sub-skill when the user needs to execute MTEB evaluations from Python, resume or inspect cache behavior while evaluating, pass encoder options, save predictions, or recover from task failures.

## Route First

- Choose tasks or benchmark objects with `mteb.get_tasks(...)` or `mteb.get_benchmark(...)`; for task discovery, filtering, public/private/beta/superseded handling, and benchmark selection, use `../tasks-and-benchmarks/SKILL.md`.
- Build or wrap the model before evaluating; for `mteb.get_model(...)`, `ModelMeta`, custom encoders, SentenceTransformer/CrossEncoder compatibility, prompts, devices, and `embed_dim`, use `../models-and-encoders/SKILL.md`.
- Prefer Python workflows here; for `mteb run`, `available-tasks`, `available-benchmarks`, batch automation, and shell equivalents, use `../cli-and-automation/SKILL.md`.
- After evaluation, inspect `ModelResult`, cached JSON, prediction files, leaderboard/submission metadata, or result loading with `../results-and-leaderboard/SKILL.md`.

## Core API

`mteb.evaluate(model, tasks, *, co2_tracker=None, raise_error=True, encode_kwargs=None, cache=ResultCache(...), overwrite_strategy="only-missing", prediction_folder=None, show_progress_bar=True, public_only=None, num_proc=None, timer=None)` returns a `ModelResult` with `task_results` and `exceptions`.

Common safe pattern:

```python
import mteb

model = mteb.get_model("mteb/baseline-random-encoder")
tasks = mteb.get_tasks(tasks=["Banking77Classification.v2"])
cache = mteb.ResultCache(cache_path="mteb-results-cache")

results = mteb.evaluate(
    model,
    tasks=tasks,
    cache=cache,
    overwrite_strategy="only-missing",
    encode_kwargs={"batch_size": 32},
    co2_tracker=False,
    raise_error=True,
)
print(results.model_name, len(results.task_results))
```

## Main Workflows

- For a first run, set an explicit `ResultCache(cache_path=...)`, keep `overwrite_strategy="only-missing"`, and set `co2_tracker=False` unless `mteb[codecarbon]` is installed.
- For resumable runs, rerun the same model/task/cache tuple with `overwrite_strategy="only-missing"`; MTEB loads compatible cached results and only evaluates missing splits/subsets.
- For cache-only inspection, use `overwrite_strategy="only-cache"`; expect a `ValueError` if the requested task/model/revision is absent or incomplete in the cache.
- For non-overwriting production runs, use `overwrite_strategy="never"`; it reuses existing complete cache entries and runs only if no compatible result exists.
- For forced recomputation, use `overwrite_strategy="always"`; this reruns the task and overwrites cached task results.
- For partial failure tolerance across many tasks, set `raise_error=False` and inspect `results.exceptions`; keep `raise_error=True` while debugging one task.
- For model encoder controls, pass `encode_kwargs={"batch_size": 64, ...}`; MTEB forwards these to task encoders and defaults `batch_size` to `32` if omitted.
- For predictions, pass `prediction_folder="predictions"`; tasks that support predictions write files named like `{task_name}_predictions.json` under that folder.
- For private datasets, set `public_only=False` only when the user has access/authentication; with `public_only=None`, private dataset download failures can warn and skip rather than hard fail.
- For data loading/transforms that support parallelism, set `num_proc=<workers>`; reduce it to `1` or `None` when multiprocessing causes dataset or platform errors.

## References

- `references/evaluation-api.md` summarizes the Python API, parameter semantics, and validation signals.
- `references/evaluation-recipes.md` contains copy-adaptable evaluation, cache, failure-tolerant, prediction, CO2, and benchmark recipes.
- `references/troubleshooting.md` maps common errors to recovery actions.
- `scripts/smoke_evaluate_with_mock.py` is a safe smoke checker for import/signature/cache/overwrite behavior without dataset downloads.

## Validation Checklist

- `import mteb` succeeds and `pip check` is clean in the active environment.
- `mteb.evaluate` exposes `cache`, `overwrite_strategy`, `prediction_folder`, `public_only`, `raise_error`, `encode_kwargs`, `co2_tracker`, and `num_proc`.
- A cache path is explicit for reproducible runs, especially when using `only-cache`, `never`, or shared CI artifacts.
- The chosen tasks are public, non-beta, and not superseded unless the user intentionally opted into private/beta/superseded coverage.
- The selected model exposes the methods required by the task modality and task type.
