---
name: "model-selection"
description: "Routes NeuralForecast model-family choice, constructor comparison,
  and optional-dependency caveat workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# model-selection

Use this sub-skill when the user asks which NeuralForecast model family to use,
how two constructors differ, whether a model supports exogenous variables or
multivariate output, or whether an optional dependency is required.

## What this route covers

- Model-family comparison and capability selection.
- Constructor differences and important input constraints.
- Multivariate vs univariate decisions.
- Optional-dependency caveats for `TimeLLM` and `xLSTM`.

## What this route does not cover

- The panel dataframe contract.
- Detailed fit/predict execution.
- Loss construction.
- Auto*/distributed search mechanics.

If the user already knows the model and just needs to run it, route to
`../core-forecasting/SKILL.md`. If the user still needs to validate columns or
exogenous layout, route to `../data-and-exogenous/SKILL.md`.

## Read these bundled references

- `../../references/model-overview.md` for the public catalog and capability
  flags.
- `../../references/api-reference.md` for verified constructor signatures.
- `references/troubleshooting.md` for `n_series`, exogenous, and optional-dep
  failures.

## Run this bundled script

- `../../scripts/list_models.py` for a live model catalog and capability dump.

## Common triggers

- "Which model should I use for this time series?"
- "What is the difference between NHITS and NBEATSx?"
- "Does this model support exogenous variables?"
- "Why does a multivariate model ask for n_series?"
- "Why can't I import TimeLLM or xLSTM?"

## Minimal route

1. Read `../../references/model-overview.md` to narrow the family.
2. Use `../../scripts/list_models.py` to confirm what the installed package
   exports.
3. Read `../../references/api-reference.md` when the constructor arguments need
   to be checked.
4. Read `references/troubleshooting.md` if the chosen model rejects the task.

## Decision cues

- If the user needs quantiles, intervals, or loss choice, route to
  `probabilistic-losses`.
- If the user needs backtesting or save/load after the model is chosen, route
  to `core-forecasting`.
- If the issue is the dataframe or exogenous columns themselves, route to
  `data-and-exogenous`.

## Safe default

When in doubt, prefer the simplest model that supports the requested data
shape. That usually means a baseline or a decomposition-style model first,
then a more expressive family if the user needs it.
