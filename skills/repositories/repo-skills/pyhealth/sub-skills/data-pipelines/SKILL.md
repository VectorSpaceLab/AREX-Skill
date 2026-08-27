---
name: data-pipelines
description: "Guides PyHealth dataset construction, sample schemas, feature
  processors, patient-safe splitting, dataloaders, and local or credential-gated
  clinical data preparation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# PyHealth data pipelines

Use this route when the request is about loading clinical data, turning patient
records into samples, processing fields, splitting data, or building a
`DataLoader`. Start with the five-stage contract: a dataset exposes structured
patients/visits/events; a task converts it to task samples; processors convert
sample fields; then models consume the resulting dictionaries.

## Workflow

1. Identify the dataset family, version, local root, expected tables/files,
   license/access, and whether a tiny local fixture is sufficient. Read
   [data formats](references/data-formats.md) and [dataset recipes](references/dataset-recipes.md).
2. Instantiate a current dataset export from `pyhealth.datasets`; do not copy
   old `MIMIC3BaseDataset`/`files=` examples without checking the current class.
3. Attach a task with `dataset.set_task(task)`; route task labels and feature
   semantics to [clinical-tasks](../clinical-tasks/SKILL.md).
4. Validate sample keys and processor schemas before training. Use
   `scripts/validate_sample_schema.py` on a local JSON fixture when possible.
5. Prefer `split_by_patient(dataset, [0.8, 0.1, 0.1], seed=...)` for longitudinal
   records, then make loaders with `get_dataloader(dataset, batch_size, shuffle=...)`.
6. Route model feature/vocabulary compatibility to
   [models-training](../models-training/SKILL.md). Never treat a successful
   remote constructor as proof of data authorization or completeness.

Read [API reference](references/api-reference.md) for current signatures,
[data formats](references/data-formats.md) for schema contracts, and
[troubleshooting](references/troubleshooting.md) before changing processors.
The bundled helpers are local/read-only by default; run `python scripts/... --help`
first.
