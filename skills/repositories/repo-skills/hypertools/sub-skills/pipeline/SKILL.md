---
name: pipeline
description: "HyperTools stage pipelines, model-spec grammar, and return-model reuse."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# HyperTools Pipeline

Use this sub-skill when the task is about the HyperTools analysis pipeline:
`manip`, `normalize`, `reduce`, `align`, `cluster`, `apply_model`, `Pipeline`,
or reusing a fitted result on held-out data.

## Route here when the user wants

- A staged analysis chain with canonical ordering.
- A reusable fitted model returned by `return_model=True`.
- A `Pipeline` object or a `pipeline=` reuse path.
- Model-spec grammar help: strings, dicts, classes, instances, lists.
- `ndims` / `random_state` behavior for reduction or clustering.
- Cluster labels, mixture proportions, or label recovery from a fitted chain.

## Route elsewhere when the user wants

- Plot styling, rendering, backends, hues, trails, animation, or surfaces: use `../visualization/`.
- Text vectorizers, semantic models, or corpus choices: use `../text/`.
- Forecasting or dedicated imputation models: use `../forecasting/`.
  - Only `impute=` at format time is in scope here.

## Read first

- `references/pipeline-reference.md` for signatures, grammars, registries,
  canonical order, and reuse rules.
- `references/workflows.md` for fit-once / reuse recipes and common chains.
- `references/troubleshooting.md` for unknown-model, `ndims`, shape, and reuse
  failures.
- `scripts/smoke_pipeline.py` for a tiny CPU end-to-end smoke check.

## Quick decision guide

1. Need to apply one model family to stacked data?
   - Use `apply_model`.
2. Need a stage-wise analysis chain in HyperTools order?
   - Use `analyze`, `reduce`, `align`, `normalize`, `manip`, or `cluster`.
3. Need to reuse the exact fit on new data?
   - Pass the fitted wrapper back as the model spec, or pass a fitted
     `Pipeline` to `analyze(..., pipeline=...)`.
4. Need to compose a named chain directly?
   - Use `Pipeline(steps)` or the dispatcher kwargs that return one.

## Canonical order

HyperTools stages always follow the same order when dispatcher kwargs are used:

`manip -> normalize -> reduce -> align -> cluster`

A few important corollaries:

- Missing-data fill happens before these stages, during format time.
- `reduce` happens before `align` in the canonical chain.
- `cluster` labels the final geometry, so `analyze(..., cluster=...)`
  returns transformed data, not labels.
- `apply_model` is separate from the stage pipeline and does not include
  `manip`, `align`, or `impute`.

## Return-model rule of thumb

- Single stage: `return_model=True` yields that stage's fitted wrapper.
- Multiple stages or cross-module kwargs: `return_model=True` yields a fitted
  `Pipeline`.
- Reuse the fitted wrapper or `Pipeline` on new data instead of refitting.

## What to remember

- Model specs can be strings, dicts, classes, instances, or lists.
- `Pipeline` stores already-resolved steps and replays them in order.
- `Pipeline.transform` reuses fitted steps; some non-transformable reducers or
  hard clusterers still have limits on held-out data.
- `analyze(..., pipeline=...)` is the replay path for a fitted chain.
- When labels are needed, recover them from the fitted cluster step.

If the task starts drifting into visualization or text/forecasting details, hand
it off to the sibling sub-skill and keep this one focused on stage dispatch,
model grammar, and reuse.
