---
name: "data-and-exogenous"
description: "Routes NeuralForecast panel schema, exogenous-variable,
  categorical, sample-weight, and scaler workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# data-and-exogenous

Use this sub-skill when the user is preparing or debugging the panel dataframe
that NeuralForecast consumes: `unique_id`, `ds`, `y`, static features, future
features, categorical variables, sample weights, availability masks, and local
scalers.

## What this route covers

- Panel dataframe layout and `TimeSeriesDataset.from_df` conversion.
- `static_df`, `futr_df`, `available_mask`, and `sample_weight` handling.
- Categorical feature declarations and cardinality checks.
- Local scaling for temporal and static features.
- pandas and Polars interoperability.

## What this route does not cover

- The forecast model choice itself.
- Auto* search or distributed Spark execution.
- Probabilistic loss construction.
- Save/load or serialization details except where they depend on the panel shape.

If the request is about which model family needs which feature set, open
`../model-selection/SKILL.md`. If the request is about `fit` / `predict`
behavior after the data is already correct, open `../core-forecasting/SKILL.md`.

## Read these bundled references

- `../../references/data-formats.md` for the long-format panel contract.
- `../../references/api-reference.md` for `TimeSeriesDataset` and data-module
  signatures.
- `references/troubleshooting.md` for schema, null, categorical, and scaler
  failures.

## Run this bundled script

- `../../scripts/validate_panel.py` for a safe dataframe-schema check.

## Common triggers

- "What columns does NeuralForecast need?"
- "My future dataframe is missing rows"
- "How do I use static exogenous variables?"
- "Why is a categorical column failing?"
- "Why do I get a scaler or mask error?"
- "Can I use Polars with NeuralForecast?"

## Minimal route

1. Read `../../references/data-formats.md` to confirm the dataframe contract.
2. Use `../../scripts/validate_panel.py` on a small sample or problematic file.
3. Read `references/troubleshooting.md` when the dataframe fails validation.

## Decision cues

- If the issue is model-specific exogenous support, route to `model-selection`.
- If the issue is a downstream `fit` or `predict` error after the data is valid,
  route to `core-forecasting`.

## Safe default

When in doubt, validate the panel first. Most NeuralForecast errors become
obvious once the `unique_id` / `ds` / `y` contract is checked explicitly.
