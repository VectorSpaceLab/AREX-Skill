---
name: igel
description: "Use Igel for classic tabular ML, FastAPI serving, and
  AutoKeras-backed Auto-ML workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Igel

Use this repo skill for the `igel` package: classic tabular fit/evaluate/predict workflows, serving a fitted model through FastAPI, and the AutoKeras-backed `IgelCNN` path.

Start here:

- [references/package-overview.md](references/package-overview.md) for the command map, install notes, and quick route decisions.
- [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting legacy install/import failures.
- [references/repo-provenance.md](references/repo-provenance.md) when checking whether this skill matches the current repository baseline.
- [references/repo-routing-metadata.json](references/repo-routing-metadata.json) for the router placement metadata used by managed import and selection logic.
- [scripts/check_env.py](scripts/check_env.py) for a safe import/help smoke check.

## Route map

1. **Classic tabular ML**: create configs, fit models, evaluate, predict, run `experiment`, export to ONNX, inspect model/metric catalogs, or use `Igel(**kwargs)` from Python. Route to [tabular-workflows](sub-skills/tabular-workflows/SKILL.md).
2. **Serving a fitted model**: start the FastAPI endpoint, call `/predict`, or use the bundled client helper. Route to [deployment](sub-skills/deployment/SKILL.md).
3. **AutoKeras / Auto-ML**: inspect `IgelCNN`, supported Auto-ML task names, or image/text/structured AutoKeras workflows. Route to [auto-ml](sub-skills/auto-ml/SKILL.md).
4. **Route selection is unclear**: use the package overview and repository routing metadata before guessing.

## Common signals

- If the user names classic sklearn-style commands such as fit, evaluate, predict, experiment, export, models, or metrics, go to tabular-workflows.
- If the user names FastAPI, /predict, host or port flags, a REST client, or model_results serving, go to deployment.
- If the user names AutoKeras, IgelCNN, ImageClassification, TextClassification, or structured-data task strings, go to auto-ml.
- If the user only wants install or import health, start with scripts/check_env.py and the cross-cutting troubleshooting reference.

## Minimal install and check

The validated package version is `igel 0.7.0` on Python 3.8-era dependencies. A compatible environment needs the legacy NumPy/SciPy/scikit-learn stack that this release expects; modern dependency resolvers can otherwise drift into incompatible versions.

Typical install from PyPI:

```bash
python -m pip install igel
```

If you are working from a local checkout, editable install is also reasonable:

```bash
python -m pip install -e .
```

After install, run the bundled smoke helper:

```bash
python scripts/check_env.py
```

For Auto-ML checks, add the helper's Auto-ML mode:

```bash
python scripts/check_env.py --auto-ml
```

## What this skill covers

- Classic `init`, `fit`, `evaluate`, `predict`, `experiment`, `export`, `models`, `metrics`, `version`, and `info` commands.
- FastAPI serving of fitted models and the `IGEL_MODEL_RESULTS_PATH` contract.
- `IgelCNN` AutoKeras task selection and the current docs/source caveat around the missing `auto-train` Click command.
- Public package artifacts such as `model_results/model.joblib`, `description.json`, `evaluation.json`, `predictions.csv`, and `model.onnx`.

## What this skill does not do

- It does not tell future agents to open the original repository docs or examples at runtime.
- It does not treat `gui` or the stale source Dockerfile as a verified self-contained deployment path.
- It does not expose repo-maintenance or publication workflows; those belong elsewhere.
