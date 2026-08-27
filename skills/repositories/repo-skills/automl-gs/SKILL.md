---
name: automl-gs
description: "Routes automl_gs tabular AutoML searches and the generated runtime
  artifacts that those searches produce."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# automl-gs

Use this root skill when the request names `automl_gs`, asks for an AutoML search on a CSV plus target field, or points at a timestamped generated folder from a previous search.

## What this skill covers

- Starting a bounded `automl_gs` / `automl_grid_search(...)` run.
- Choosing between the supported search frameworks: TensorFlow or XGBoost.
- Inspecting the generated `model.py`, `pipeline.py`, encoders, metadata, and prediction outputs.
- Troubleshooting package import problems, backend mismatches, and generated-folder runtime issues.

## Route to a sub-skill

- Use [grid-search](sub-skills/grid-search/SKILL.md) for a new search from `CSV + target`.
- Use [generated-artifacts](sub-skills/generated-artifacts/SKILL.md) for a completed timestamped folder and its `train` / `predict` commands.

## Read these references when needed

- [workflow-overview](references/workflow-overview.md) for the quick package map, supported outputs, and when to choose each route.
- [troubleshooting](references/troubleshooting.md) for install/import issues, backend mismatches, and other cross-cutting failures.
- [repo-provenance](references/repo-provenance.md) when checking whether this skill matches the current repository revision or before refreshing it.

## Install and smoke check

Install the package in the active environment, then add the backend you actually plan to use:

```bash
pip install -e .
python -m pip install xgboost
```

Use TensorFlow only when you need to exercise the legacy TensorFlow-generated path.

For a quick sanity check, run the bundled helper. Pass the backend you actually installed when you want a backend import check:

```bash
python scripts/check_install.py --backend xgboost
```

## Fast routing hints

- If the user says “run automl-gs on this CSV”, “search hyperparameters”, or “pick a framework”, route to **grid-search**.
- If the user says “train the generated model”, “predict from the exported folder”, or mentions `model.py` / `pipeline.py`, route to **generated-artifacts**.
- If import fails, `automl_gs -h` fails, or a subprocess launches the wrong Python, read **troubleshooting** first.

## Public surface in one line

`automl_gs` turns a CSV and target field into a generated model folder plus `automl_results.csv`; the exported folder then owns training, prediction, and encoder loading.
