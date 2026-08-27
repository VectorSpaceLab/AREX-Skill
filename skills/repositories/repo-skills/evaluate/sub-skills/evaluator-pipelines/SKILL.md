---
name: evaluator-pipelines
description: "Use evaluate.evaluator and EvaluationSuite to evaluate model
  pipelines on datasets across supported NLP, vision, and audio tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Evaluator Pipelines

Use this sub-skill when the task is to evaluate a model, model id, prebuilt `transformers.Pipeline`, or compatible callable against a dataset using `evaluate.evaluator(...)`, or to run a group of evaluator subtasks with `EvaluationSuite`.

## Route

- Use `references/evaluator-workflows.md` for end-to-end evaluator and suite patterns, including preloaded datasets, non-default columns, devices, bootstrap, label mappings, and subtasks.
- Use `references/api-reference.md` for supported tasks, default metrics, task-specific columns, common `compute(...)` arguments, and `SubTask`/`EvaluationSuite` signatures.
- Use `references/troubleshooting.md` before running expensive or network-dependent evaluations, especially when optional model backends, dataset columns, devices, or bootstrap are involved.
- Use `scripts/inspect_evaluator_tasks.py` to print the installed evaluator task registry without downloading models or datasets.

## Boundaries

- This sub-skill covers evaluator pipelines, task-specific dataset schemas, performance metrics, device handling, and evaluation suites.
- For low-level metric or comparison module calls such as `metric.compute(...)`, route to `../module-computation/`.
- For arbitrary `evaluate.load(...)` module discovery and loading behavior, route to `../module-loading/`.
- For authoring, packaging, or publishing custom evaluation modules, route to `../hub-and-cli/`.

## Quick Start

```python
from evaluate import evaluator

clf = evaluator("text-classification")
results = clf.compute(
    model_or_pipeline=pipe_or_model_id,
    data=dataset,
    metric="accuracy",
    input_column="review_text",
    label_column="gold_label",
    label_mapping={"NEGATIVE": 0, "POSITIVE": 1},
    device=-1,
)
```

`compute(...)` returns metric scores plus pipeline timing keys such as `total_time_in_seconds`, `samples_per_second`, and `latency_in_seconds`. Pass `strategy="bootstrap"` only when the extra scipy bootstrap cost is acceptable.
