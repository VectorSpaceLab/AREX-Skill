# Data formats and validation

A raw patient record is organized around a patient identifier, visits, event
collections, codes, and timestamps. A task sample normally carries identity
fields such as `patient_id` and `visit_id`/`record_id`, processed input fields,
and a task output such as `label` or a task-specific target. Exact keys are task
contracts, not universal PyHealth constants.

## Minimum fixture

Use a de-identified synthetic fixture with:

```json
{
  "patient_id": "p1",
  "visit_id": "v1",
  "conditions": ["I10", "E11"],
  "event_time": [0.0, 1.0],
  "label": 1
}
```

Adapt the fields and processor aliases to the task. The important assertions
are: required keys exist; patient and record identifiers are stable; timestamps
are parseable and ordered or explicitly normalized; code fields are lists when
a sequence processor expects lists; labels match the selected task mode; and
no split contains the same patient in two partitions.

## SampleBuilder schema

`input_schema` and `output_schema` map field names to a processor alias, a
`FeatureProcessor` class/instance, or `(spec, kwargs)` such as a code mapping.
`SampleBuilder.fit` validates keys and fits processors. Accessing fitted
processor/index properties before `fit` raises `RuntimeError`. `IgnoreProcessor`
fields are removed from a `SampleDataset`'s active schemas.

## External layouts

MIMIC, eICU, OMOP, FHIR, MEDS, PhysioNet, imaging, and EEG datasets have
source-specific file names, permissions, and table schemas. Record the source
layout and package configuration before running. Missing or empty files should
produce a preflight failure rather than silently yielding zero samples. Never
bundle PHI, credentials, or a private dataset into an operating skill.
