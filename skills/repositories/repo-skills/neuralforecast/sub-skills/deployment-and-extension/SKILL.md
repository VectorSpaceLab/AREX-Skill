---
name: "deployment-and-extension"
description: "Routes NeuralForecast save/load, serialization, export, logging,
  and model-extension workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# deployment-and-extension

Use this sub-skill when the user wants to save or reload a fitted forecast,
export a model, log to MLflow, or understand how to extend NeuralForecast with a
new model or docs update.

## What this route covers

- `NeuralForecast.save` and `NeuralForecast.load`.
- Save/load portability and overwrite behavior.
- Optional export surfaces such as ONNX or MLflow when the user explicitly
  needs them.
- Maintainer-facing extension guidance for adding or updating models.

## What this route does not cover

- The core forecast loop itself.
- Dataframe preparation.
- Model selection.
- Auto* tuning or distributed execution.

If the user only needs to run the saved model, route to
`../core-forecasting/SKILL.md`. If the user first needs the panel schema or
future exogenous layout, route to `../data-and-exogenous/SKILL.md`.

## Read these bundled references

- `../../references/deployment-extension.md` for serialization and optional
  export notes.
- `../../references/workflows.md` for save/load and quickstart recipes.
- `references/troubleshooting.md` for save/load, optional-dependency, and docs
  failures.

## Run this bundled script

- `../../scripts/check_serialization.py` for a small save/load round-trip.
- `../../scripts/core_smoke.py` when you want to confirm a model still fits and
  predicts before serializing it.

## Common triggers

- "Can I save this fitted model?"
- "How do I reload a NeuralForecast bundle?"
- "Why did my checkpoint path fail?"
- "How do I add a new model to the package?"
- "How do I make the docs or export workflow run again?"

## Minimal route

1. Read `../../references/deployment-extension.md` for the portability or
   extension path.
2. Use `../../scripts/check_serialization.py` for a safe round-trip smoke.
3. Read `references/troubleshooting.md` when the save/load or optional export
   workflow fails.

## Decision cues

- If the issue is model family selection, route to `model-selection`.
- If the issue is the panel dataframe, route to `data-and-exogenous`.
- If the issue is a forecast run before serialization, route to
  `core-forecasting`.

## Safe default

When in doubt, confirm save/load first with a temporary directory and a tiny
model, then move on to optional export or maintainer work only if needed.
