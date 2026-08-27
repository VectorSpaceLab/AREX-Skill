# Task workflows

## Built-in task

```python
from pyhealth.datasets import MIMIC3Dataset
from pyhealth.tasks import MortalityPredictionMIMIC3

base = MIMIC3Dataset(root="/authorized/local/root")
samples = base.set_task(MortalityPredictionMIMIC3())
print(len(samples), samples[0].keys())
```

The exact dataset arguments/tables vary by release; use the dataset route and
validate a small local cohort before a full transformation. A task can produce
multiple samples per patient, so patient-level splitting is mandatory for most
longitudinal evaluation.

## Custom task sketch

```python
from pyhealth.tasks import BaseTask

class TinyTask(BaseTask):
    task_name = "tiny_binary"
    input_schema = {"conditions": "sequence"}
    output_schema = {"label": "binary_label"}

    def __call__(self, patient):
        # Return [] when the patient has no valid observation.
        return [{"patient_id": patient.patient_id,
                 "conditions": ["I10"], "label": 1}]
```

Use actual `Patient`/visit fields from the selected dataset and processor
aliases. The example is a contract sketch, not a clinical cohort definition.
Add deterministic tests for empty patients, missing features, date boundaries,
label balance, and patient identity. Do not infer clinical meaning from a
synthetic label.

## Handoff checklist

- task class and package version recorded;
- source access and expected source tables validated;
- task sample keys/labels/dtypes inspected;
- patient IDs are disjoint across splits;
- model input contract and output mode recorded;
- metric family and threshold/calibration protocol selected;
- credential/network/large-run gates accepted or explicitly skipped.
