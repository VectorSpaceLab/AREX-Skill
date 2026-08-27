---
name: clinical-tasks
description: "Guides PyHealth task selection, task-to-dataset attachment,
  clinical label and feature contracts, patient-safe sample splits, and bounded
  custom task definitions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# PyHealth clinical tasks

Use this route when the user asks for mortality, readmission, length-of-stay,
drug recommendation, coding, survival, de-identification, EEG/CXR/variant,
patient-linkage, or another task-specific sample pipeline.

## Workflow

1. Identify the source dataset and task family; read [task catalog](references/task-catalog.md)
   for current public exports and data prerequisites.
2. Construct the dataset in [data-pipelines](../data-pipelines/SKILL.md), then
   instantiate the task and call `dataset.set_task(task)`.
3. Inspect one task sample: identity fields, feature keys, labels/targets,
   dtypes, and processor aliases. Use `scripts/validate_task_samples.py` for a
   local JSON contract before invoking a model.
4. Split by patient and route model/vocabulary compatibility to
   [models-training](../models-training/SKILL.md). Route metric semantics to
   [evaluation-interpretability](../evaluation-interpretability/SKILL.md).
5. For a new task, subclass `BaseTask`, define `task_name`, `input_schema`,
   `output_schema`, and `__call__(patient)`, and optionally implement
   `pre_filter` or pass code mappings. Test on synthetic patients first.

Credentialed MIMIC/eICU/OMOP/PhysioNet/MEDS data and long benchmark examples
are not package-import tests. Preserve access and schema gates explicitly.
Read [workflows](references/workflows.md), [API details](references/api-reference.md),
and [troubleshooting](references/troubleshooting.md).
