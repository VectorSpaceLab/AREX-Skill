# Igel package overview

Igel is a small Python ML package that wraps classic scikit-learn workflows behind a Click CLI and a thin Python API, and also includes an AutoKeras-backed `IgelCNN` path plus a FastAPI serving surface.

## Public command families

| Command family | Route |
| --- | --- |
| `init`, `fit`, `evaluate`, `predict`, `experiment`, `export`, `models`, `metrics`, `version`, `info` | [tabular-workflows](../sub-skills/tabular-workflows/SKILL.md) |
| `serve` and HTTP prediction calls | [deployment](../sub-skills/deployment/SKILL.md) |
| `IgelCNN`, AutoKeras task names, image/text/structured Auto-ML | [auto-ml](../sub-skills/auto-ml/SKILL.md) |
| `gui`, Docker notes, or stale container/build paths | troubleshooting only unless a future revision adds a dedicated route |

## Verified package facts

- Distribution / import name: `igel`
- Version: `0.7.0`
- Root Python API: `from igel import Igel, models_dict, metrics_dict`
- Auto-ML API: `from igel.auto import IgelCNN`
- Serving API: `igel.servers.fastapi_server`
- CLI help surface includes `init`, `fit`, `evaluate`, `predict`, `experiment`, `export`, `models`, `metrics`, `serve`, `gui`, `version`, and `info`

## Install notes

The verified package version is from a legacy Python 3.8-era stack. When a modern resolver or a too-new NumPy/SciPy pair breaks importability, use the troubleshooting reference and the smoke checker before trying to use the skill.

A simple public install command is:

```bash
python -m pip install igel
```

If you are using a local checkout of this same version, editable install is acceptable:

```bash
python -m pip install -e .
```

## Artifact conventions

Classic tabular runs write results relative to the working directory:

- `model_results/model.joblib`
- `model_results/description.json`
- `model_results/evaluation.json`
- `model_results/predictions.csv`
- `model_results/model.onnx`

Serving uses the same fitted `model_results/` directory plus the `IGEL_MODEL_RESULTS_PATH` environment variable. Auto-ML uses `model/` or `model.h5` plus a description JSON.

## When to read this file

Read this when you need a quick route map, install reminder, or command-family overview before switching to a focused sub-skill.
