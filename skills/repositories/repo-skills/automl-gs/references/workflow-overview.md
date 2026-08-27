# automl-gs Workflow Overview

This is the fastest orientation page for the repo skill. Read it when you want the package-level map before choosing a sub-skill.

## What the package does

`automl_gs` reads a local CSV plus a target field, infers a tabular problem type, samples discrete hyperparameter combinations, and writes:

- `automl_results.csv` for trial-by-trial search results.
- A timestamped best-model folder containing generated `model.py`, `pipeline.py`, encoders, metadata, and a framework model artifact.

## Main routes

| User intent | Route |
| --- | --- |
| Start a new AutoML search on a CSV | [grid-search](../sub-skills/grid-search/SKILL.md) |
| Work inside the generated folder after a search | [generated-artifacts](../sub-skills/generated-artifacts/SKILL.md) |

## Supported search frameworks

- TensorFlow via `tf.keras` in the source templates.
- XGBoost with histogram tree method.

For this skill generation, the verified CPU path is the XGBoost route. The TensorFlow templates remain documented because they are part of the package surface, but they are more compatibility-sensitive.

## Typical search flow

1. Install the package and the backend you intend to use.
2. Run `automl_gs <csv> <target>` or `automl_grid_search(...)`.
3. Inspect `automl_results.csv` for trial metrics and the timestamped best-model folder for the exported runtime files.
4. Switch to **generated-artifacts** if you want to retrain or predict from the exported folder.

## Typical generated-folder flow

1. `cd` into the timestamped folder.
2. Run `python model.py -d <csv> -m train` to refresh encoders and model files.
3. Run `python model.py -d <csv> -m predict -t csv` or `-t json` to write predictions.

## Quick sanity check

Use [scripts/check_install.py](../scripts/check_install.py) to verify the package import, CLI help, and optional backend import before you start a longer search.
