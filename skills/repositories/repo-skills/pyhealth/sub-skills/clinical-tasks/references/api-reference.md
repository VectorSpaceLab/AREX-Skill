# Clinical-task API reference

`pyhealth.tasks` exports `BaseTask` and built-in task classes for EHR,
multimodal, coding, survival, recommendation, EEG, imaging, NLP, variant, and
linkage workflows. Exact constructor names are versioned; inspect the selected
class before execution and do not copy a 1.x evaluator API.

## BaseTask contract

Current `BaseTask` has class-level `task_name`, `input_schema`, and
`output_schema` contracts. Its constructor accepts:

```text
BaseTask(code_mapping: Optional[Dict[str, Tuple[str, str]]] = None)
```

`code_mapping` maps a field to `(source_vocabulary, target_vocabulary)` and
upgrades a sequence schema to pass that mapping to its processor. The abstract
`__call__(patient) -> List[Dict]` produces zero or more sample dictionaries;
`pre_filter(df: polars.LazyFrame)` may narrow source rows before patient
processing.

A task sample should retain stable `patient_id` and visit/record identity where
available, include every field promised by `input_schema` and `output_schema`,
and use output names expected by the selected model. The task, not the model,
owns label semantics and cohort/date filtering.

## Attachment

The current pipeline attaches a task through the dataset's `set_task(task)`
operation. After transformation, inspect the sample dataset's length, sample
keys, and task metadata. Then use `split_by_patient` from the data route. Do not
split raw visits first and assume the task will preserve patient disjointness.
