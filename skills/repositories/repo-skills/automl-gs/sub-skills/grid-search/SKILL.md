---
name: grid-search
description: "Run automl_gs / automl_grid_search on a CSV and target field."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Grid Search

Use this sub-skill to launch a bounded automl-gs search on a local CSV, choose a framework, infer or override the target metric, and inspect the trial log.

## Route here for

- `automl_gs` CLI and `automl_grid_search(...)`
- framework selection (`tensorflow`, `xgboost`)
- target-metric inference, override, and result selection
- trial count, epoch budget, and output-folder discovery
- smoke checks for import/signature, CLI help, and tiny offline XGBoost search

## Do not handle here

- Post-search use of generated `model.py`, `pipeline.py`, encoder JSON, or retraining/prediction on the exported artifacts; route to [generated-artifacts](../generated-artifacts/SKILL.md).

## Operating workflow

1. Read [api-reference](references/api-reference.md) for install/import notes, exact call signatures, and typing overrides.
2. Read [hyperparameters-and-metrics](references/hyperparameters-and-metrics.md) for search-space rules, metric direction, and output layout.
3. Use [troubleshooting](references/troubleshooting.md) when imports, dependencies, type inference, or CSV paths go wrong.
4. For a fast smoke run, start from `scripts/run_tiny_xgboost_search.py`.

Keep this sub-skill focused on search-time behavior. Handle exported artifacts elsewhere.
