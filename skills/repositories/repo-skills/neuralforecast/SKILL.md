---
name: "neuralforecast"
description: "Routes NeuralForecast time-series forecasting, data,
  model-selection, loss, tuning, and deployment workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# NeuralForecast

Use this skill when the task is about the `neuralforecast` package and its
panel time-series forecasting workflows: fitting models, predicting horizons,
choosing model families, validating panel data, selecting losses, tuning with
Ray or Optuna, working with distributed Spark data, or saving and reloading a
fitted forecast bundle.

## Install

For a public install:

```bash
python -m pip install neuralforecast
```

For a local checkout:

```bash
python -m pip install -e .
```

The package requires Python 3.10+ and is routinely inspected here with Python
3.11. Install optional extras only when the route needs them, such as `spark`
for distributed workflows or `onnx` / `mlflow` / `transformers` / `xlstm` for
specialized extension recipes.

## Minimal import check

```bash
python -I -c "from neuralforecast import NeuralForecast; from neuralforecast.models import NHITS; from neuralforecast.utils import generate_series; print('ok')"
```

If that fails, read `references/troubleshooting.md` before doing anything else.

## Route map

| User task family | Read this sub-skill | Typical helper |
| --- | --- | --- |
| Fit, predict, backtest, save/load, simulate, explain | `sub-skills/core-forecasting/SKILL.md` | `scripts/core_smoke.py` |
| Panel dataframe layout, exogenous variables, categorical features, scalers | `sub-skills/data-and-exogenous/SKILL.md` | `scripts/validate_panel.py` |
| Choose a model family or compare constructors | `sub-skills/model-selection/SKILL.md` | `scripts/list_models.py` |
| Quantile, distribution, robust, and interval losses | `sub-skills/probabilistic-losses/SKILL.md` | `scripts/check_losses.py` |
| Auto* search, Ray/Optuna, or Spark distributed paths | `sub-skills/tuning-and-distributed/SKILL.md` | `scripts/check_auto_config.py` |
| Save/load, ONNX, MLflow, docs, and extension work | `sub-skills/deployment-and-extension/SKILL.md` | `scripts/check_serialization.py` |

## Shared references

- `references/repo-provenance.md` before deciding whether the skill matches the
  current checkout or should be refreshed.
- `references/repo-routing-metadata.json` for managed repo-skill routing.
- `references/api-reference.md` for verified signatures.
- `references/data-formats.md` for the panel schema and exogenous-column rules.
- `references/model-overview.md` for the model catalog and capability flags.
- `references/losses-reference.md` for loss and prediction-interval rules.
- `references/workflows.md` for compact end-to-end recipes.
- `references/tuning-distributed.md` for Auto*, Ray, Optuna, and Spark details.
- `references/deployment-extension.md` for serialization and extension guidance.
- `references/troubleshooting.md` for cross-cutting failures and recovery.

## Shared scripts

- `scripts/core_smoke.py` — tiny fit/predict smoke, good first check for core
  package health.
- `scripts/validate_panel.py` — dataframe schema and panel-layout validator.
- `scripts/list_models.py` — print the exported model catalog and capability
  flags.
- `scripts/check_losses.py` — deterministic loss sanity checks.
- `scripts/check_auto_config.py` — Auto* and backend option sanity check.
- `scripts/check_serialization.py` — save/load round-trip smoke.

## How to route

1. Decide whether the request is about the panel schema, model choice, core
   forecasting, loss selection, tuning/distributed execution, or deployment.
2. Read the matching sub-skill first.
3. Use the shared references for API signatures, workflows, and troubleshooting.
4. Use the shared scripts when a safe tiny smoke or validator will answer the
   question faster than reading prose.

## Fast defaults

- If the user is unsure which model to use, open `model-selection` first.
- If the user shows a dataframe or schema error, open `data-and-exogenous`.
- If the user asks for "the usual quickstart," open `core-forecasting` and run
  `scripts/core_smoke.py`.
- If the user asks about quantiles or intervals, open `probabilistic-losses`.
- If the user asks about Ray, Optuna, Spark, or Auto*, open
  `tuning-and-distributed`.
- If the user asks about save/load or extending the package, open
  `deployment-and-extension`.

## Staleness check

Read `references/repo-provenance.md` before trusting version-sensitive details.
If the current checkout commit or public API has moved on, refresh this skill.
