---
name: "core-forecasting"
description: "Routes NeuralForecast fit, predict, cross-validation, in-sample
  prediction, simulation, explanation, and save/load workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# core-forecasting

Use this sub-skill when a user wants to run the main NeuralForecast workflow
end to end: build a `NeuralForecast` object, fit models, predict future values,
run cross-validation, inspect in-sample forecasts, simulate paths, explain
predictions, or save and reload fitted models.

## What this route covers

- `NeuralForecast(...)` construction.
- `fit`, `predict`, `cross_validation`, and `predict_insample`.
- `simulate` and `explain` for supported models.
- `save` and `load` for persistence and portability.
- Validation failures that belong to the core workflow, such as missing
  validation data for early stopping, short series, and future exogenous
  mismatches.

## What this route does not cover

- Data schema design, categorical encodings, and scaler setup in depth.
- Choosing a model family or understanding model-specific constraints.
- Loss construction details beyond what is needed to use the core workflow.
- Auto* tuning or distributed Spark/Ray execution.

If the request is really about dataframe layout, exogenous columns, or
scaling, open `../data-and-exogenous/SKILL.md` instead. If the request is about
which model family to use, open `../model-selection/SKILL.md`.

## Read these bundled references

- `../../references/api-reference.md` for verified constructor and method
  signatures.
- `../../references/workflows.md` for quickstart, cross-validation, prediction
  intervals, simulation, explanation, and save/load recipes.
- `references/troubleshooting.md` for core-workflow failures and recovery steps.

## Run these bundled scripts

- `../../scripts/core_smoke.py` for a tiny fit/predict smoke check.
- `../../scripts/check_serialization.py` for a small save/load round-trip.

## Common triggers

- "fit a NeuralForecast model"
- "predict the next horizon"
- "cross-validate this forecast"
- "save and load the fitted model"
- "simulate forecast paths"
- "why does early stopping fail"
- "why is predict_insample empty"

## Minimal route

1. Read `../../references/workflows.md` for the exact command pattern.
2. Read `../../references/api-reference.md` when you need constructor or method
   arguments.
3. Use `../../scripts/core_smoke.py` when you need a safe tiny smoke.
4. Use `references/troubleshooting.md` when the user shows an error.

## Decision cues

- If the user needs `unique_id`, `ds`, `y`, or exogenous column rules, route to
  `data-and-exogenous`.
- If the user needs a model choice, alias, or capability comparison, route to
  `model-selection`.
- If the user needs quantiles, intervals, or loss choices, route to
  `probabilistic-losses`.
- If the user needs Ray, Optuna, or Spark tuning, route to
  `tuning-and-distributed`.

## Safe default

When in doubt, use `../../scripts/core_smoke.py` first. It is the fastest way
to confirm that the core package, a model, and a forecast round-trip all work
in this environment.
