# Evaluator Workflows

Evaluator pipelines wrap model inference, prediction post-processing, metric loading/computation, and simple timing measurements. They are convenient when a future agent has a supported task, a dataset, and either a model identifier, model object, prebuilt pipeline, or callable pipeline-compatible object.

## Inspect the Installed Registry

Run the bundled helper before committing to a task name or default metric:

```bash
python skills/evaluate/sub-skills/evaluator-pipelines/scripts/inspect_evaluator_tasks.py
python skills/evaluate/sub-skills/evaluator-pipelines/scripts/inspect_evaluator_tasks.py --json
```

The script imports `evaluate.evaluator`, reads the supported task registry, and prints evaluator class names and default metrics. It does not load models, datasets, metrics, or remote resources.

## Single Evaluator Pattern

```python
from evaluate import evaluator

task_evaluator = evaluator("text-classification")
results = task_evaluator.compute(
    model_or_pipeline=pipe_or_model_id,
    data=dataset_or_dataset_name,
    subset=None,
    split="validation[:100]",
    metric="accuracy",
    strategy="simple",
    device=-1,
    input_column="text",
    label_column="label",
    label_mapping={"NEGATIVE": 0, "POSITIVE": 1},
)
```

Checklist:

1. Choose a task from `get_supported_tasks()` or the registry helper.
2. Prefer a preloaded `datasets.Dataset` when network access or dataset download is constrained; `subset` and `split` are ignored for preloaded datasets.
3. Pass a model id or model object only when model downloads/backends are available; pass a prebuilt pipeline when you need precise tokenizer, feature extractor, batch, or device control.
4. Override column names to match the dataset schema.
5. Add `label_mapping` when pipeline output labels are strings but metric references are ids or another label convention.
6. Review timing keys separately from metric quality scores because they include pipeline preprocessing/postprocessing and are hardware-dependent.

## Model or Pipeline Initialization

`model_or_pipeline` can be:

- `None`: evaluator builds the default `transformers.pipeline(task, device=...)`; this may trigger downloads.
- `str`: evaluator builds a `transformers.pipeline` with the model id/path; this may trigger downloads.
- pretrained model object: evaluator builds a pipeline with the model plus optional tokenizer or feature extractor.
- prebuilt `Pipeline`: evaluator uses it as-is and ignores tokenizer/feature extractor arguments.
- callable: evaluator assumes pipeline-like behavior and calls it directly.

If passing a prebuilt pipeline, make sure `pipe.task` matches the evaluator task. Translation pipelines are accepted when their task starts with `translation`.

## Device Selection

- `device=None` lets the evaluator infer GPU `0` if torch/tensorflow reports a GPU, otherwise CPU `-1`.
- `device=-1` forces CPU for evaluator-created pipelines.
- `device=0`, `1`, ... selects a CUDA device for evaluator-created pipelines.
- If `model_or_pipeline` is already a `Pipeline`, initialize that pipeline on the desired device; passing a conflicting non-CPU `device` to `compute(...)` raises a mismatch error.

## Strategy and Bootstrap

The default `strategy="simple"` computes metric values once. With `strategy="bootstrap"`, each metric key becomes a dict containing:

- `score`: the original metric value.
- `confidence_interval`: scipy bootstrap low/high interval.
- `standard_error`: scipy bootstrap standard error.

Use small `n_resamples` for smoke tests and larger values only when runtime is acceptable. Bootstrap needs scipy and repeatedly calls the metric, so it can be expensive on large datasets or complex metrics.

## Preloaded Dataset with Non-Default Columns

Use this pattern when downloads are not allowed and the dataset schema does not match evaluator defaults:

```python
from datasets import Dataset
from evaluate import evaluator

examples = Dataset.from_dict({
    "review_text": ["great", "bad"],
    "gold_label": [1, 0],
})

results = evaluator("text-classification").compute(
    model_or_pipeline=prebuilt_text_classification_pipeline,
    data=examples,
    metric="accuracy",
    input_column="review_text",
    label_column="gold_label",
    label_mapping={"NEGATIVE": 0, "POSITIVE": 1},
    device=None,
)
```

Use `second_input_column` for paired-text tasks such as RTE/MNLI-style classification.

## EvaluationSuite Pattern

An evaluation suite is a Python module defining a concrete `Suite(evaluate.EvaluationSuite)` class whose `self.suite` is a list of `SubTask` objects. Load it by local path or Hub id, then run one model/pipeline across all subtasks:

```python
from evaluate import EvaluationSuite

suite = EvaluationSuite.load("path-or-hub-id")
results = suite.run(model_or_pipeline=pipe_or_model_id)
```

A suite subtask looks like:

```python
from evaluate.evaluation_suite import SubTask

SubTask(
    task_type="text-classification",
    data="glue",
    subset="sst2",
    split="validation[:10]",
    data_preprocessor=None,
    args_for_task={
        "metric": "accuracy",
        "input_column": "sentence",
        "label_column": "label",
        "label_mapping": {"LABEL_0": 0, "LABEL_1": 1},
    },
)
```

Suite notes:

- `task_type` must be a supported evaluator task.
- `data` must be a dataset name string or an already-instantiated `Dataset`.
- `subset` maps to the dataset config name and `split` can include split slicing.
- `data_preprocessor`, when present, is applied with `Dataset.map(...)` after loading by dataset name.
- `args_for_task` is passed to the task evaluator and must include task-specific column/metric arguments as needed.
- `EvaluationSuite.run(model_or_pipeline)` returns a list of result dictionaries and adds `task_name` plus `data_preprocessor` fields.

Be careful: the current suite runner mutates each subtask's `args_for_task` by inserting `model_or_pipeline`, `data`, `subset`, and `split`, so avoid reusing the same mutable dict across unrelated suite instances.

## Synthetic Usability Cases

- Build a text-classification evaluator call over a preloaded `Dataset` with columns `review_text` and `gold_label`, a fake/prebuilt pipeline returning `NEGATIVE`/`POSITIVE`, and a `label_mapping` that maps those labels to integer references. Verify no dataset/model downloads are required.
- Diagnose a planned `question-answering` bootstrap run where no torch/tensorflow/flax backend is installed, the model id would need a network download, and `n_resamples` is high. The expected answer should recommend preloading a compatible pipeline/backend, using a local dataset slice, and running `strategy="simple"` or a tiny bootstrap smoke test first.
