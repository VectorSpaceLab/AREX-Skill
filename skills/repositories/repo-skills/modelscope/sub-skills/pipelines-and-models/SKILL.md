---
name: pipelines-and-models
description: "Use ModelScope inference pipelines, model/preprocessor registries,
  output keys, and safe local custom pipeline smoke checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Pipelines and Models

Use this sub-skill when a task needs ModelScope inference or registry behavior:
constructing `pipeline(...)`, loading `Model.from_pretrained(...)` or
`Preprocessor.from_pretrained(...)`, choosing task constants, reading standard
`OutputKeys`, validating batching behavior, or creating a local custom pipeline
smoke check.

## Fast routing

- Start with [references/workflows.md](references/workflows.md) for the decision
  flow: default task model, explicit hub/local model, local config, explicit
  preprocessor, custom `pipeline_name`, device, revision, optional dependency,
  and `trust_remote_code` choices.
- Use [references/api-reference.md](references/api-reference.md) for signatures,
  call flow, registry construction, config loading, and trust boundaries.
- Use [references/task-output-reference.md](references/task-output-reference.md)
  for `Tasks`, input checking, output key conventions, and safe result handling.
- Use [references/troubleshooting.md](references/troubleshooting.md) when a
  registry lookup, optional backend import, CUDA/device selection, hub download,
  Python config, plugin, or output-key check fails.
- Run [scripts/custom_pipeline_smoke.py](scripts/custom_pipeline_smoke.py) to
  verify local custom pipeline registration without network, training, downloads,
  CUDA, or writes outside a temporary directory.

## Scope boundaries

This sub-skill covers inference and registry workflows only. For template-file
creation with ModelScope CLI, route to `../customization-and-development/SKILL.md`.
For training, evaluation loops, metrics-in-trainer usage, or checkpoint training
outputs, route to `../training-and-evaluation/SKILL.md`. For detailed dataset
loading, `MsDataset.load(...)`, dataset schemas, or dataset cache behavior, route
to `../datasets-config/SKILL.md`.

CUDA, domain-specific accelerator execution, and heavyweight model downloads are
optional and unverified in this production scope. Prefer explicit CPU execution
for portable smoke checks.
