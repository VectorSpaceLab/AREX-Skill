---
name: multitask-models
description: "DeepCTR multitask workflows for SharedBottom, ESMM, MMOE, and PLE."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Multitask Models

Use this sub-skill for DeepCTR multi-output learning tasks that need shared
feature inputs and task-specific heads.

## Covers

- SharedBottom, ESMM, MMOE, and PLE
- task name / task type alignment
- binary vs regression validation where supported
- shared feature reuse from one `dnn_feature_columns` list
- compile / fit / evaluate / predict for multi-output models
- tiny synthetic smoke checks via the bundled script

## Route elsewhere

- Single-output CTR or regression model selection: `keras-model-workflows`
- Feature column construction details: `data-and-feature-columns`
- Estimator workflows: `estimator-workflows`

## Read first

- [API reference](references/api-reference.md): constructor signatures, task
  validation, and output name order
- [Workflows](references/workflows.md): two-label preprocessing,
  compile/fit/evaluate/predict patterns, and model selection
- [Troubleshooting](references/troubleshooting.md): task-list, string sparse,
  loss-order, and output-shape failures

## Smoke check

- [Tiny multitask smoke](scripts/multitask_tiny_smoke.py): synthetic checks for
  SharedBottom, ESMM, MMOE, and PLE
