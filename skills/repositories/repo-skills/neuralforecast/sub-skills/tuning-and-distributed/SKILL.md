---
name: "tuning-and-distributed"
description: "Routes NeuralForecast Auto*, Ray, Optuna, and Spark distributed workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# tuning-and-distributed

Use this sub-skill when the user wants Auto* hyperparameter search, backend
resource configuration, or distributed Spark execution for NeuralForecast.

## What this route covers

- `BaseAuto` and the `Auto*` wrappers.
- `RayOptions` and `OptunaOptions`.
- `DistributedConfig` and Spark-backed distributed paths.
- Resource, trial, and backend selection for tuning jobs.

## What this route does not cover

- Panel dataframe preparation.
- Model-family choice beyond what is needed to size the search space.
- Loss mathematics.
- Core single-model fit/predict details unless they are needed to explain the
  tuning backend.

If the user only needs to run a model after the search is configured, route to
`../core-forecasting/SKILL.md`. If the user still needs to fix the panel or
exogenous columns, route to `../data-and-exogenous/SKILL.md`.

## Read these bundled references

- `../../references/tuning-distributed.md` for the backend matrix and workflow
  notes.
- `../../references/api-reference.md` for the verified Auto*/backend signatures.
- `references/troubleshooting.md` for backend, resource, and search-space
  failures.

## Run this bundled script

- `../../scripts/check_auto_config.py` for a conservative Auto* configuration
  check.

## Common triggers

- "I need AutoNHITS with Ray"
- "Can I use Optuna instead of Ray?"
- "How do I configure GPU trials?"
- "Can I run this with Spark?"
- "Why does cross-validation with use_fitted fail?"

## Minimal route

1. Read `../../references/tuning-distributed.md`.
2. Use `../../scripts/check_auto_config.py` to confirm the backend option shape.
3. Read `references/troubleshooting.md` when a tuning or distributed job fails.

## Decision cues

- If the issue is the model family itself, route to `model-selection`.
- If the issue is the panel dataframe or future exogenous layout, route to
  `data-and-exogenous`.
- If the user only wants a quick fit on a single model, route to
  `core-forecasting`.

## Safe default

When in doubt, start with one tiny trial and the smallest plausible resource
hint. Keep the configuration conservative until the search path is proven.
