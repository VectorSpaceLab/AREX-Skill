---
name: statsmodels-logit-workflow
description: "Fit the admissions logistic regression example with pandas and
  statsmodels, using bundled CSV fixtures, schema validation, prestige dummy
  encoding, intercept handling, prediction CSV output, and optional
  non-interactive plots."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# statsmodels-logit-workflow

Use this sub-skill for the admissions logistic-regression example built with `pandas` and `statsmodels`.

## Route here for

- Loading the bundled admissions train/test CSV fixtures.
- Validating the required schema and normalizing `prestige` values.
- Fitting `statsmodels.api.Logit` with an intercept and aligned dummy columns.
- Writing a prediction CSV with probability and thresholded labels.
- Generating optional PNG diagnostics without an interactive display.

## Route away

- scikit-learn or Kaggle-style classifier pipelines: `../kaggle-linear-models/SKILL.md`
- Tutorial/resource navigation or Python snippet cleanup: `../tutorial-resource-map/SKILL.md`

## Start here

- End-to-end recipe: `references/workflows.md`
- Column schema and output layout: `references/data-formats.md`
- Failure diagnosis: `references/troubleshooting.md`
- Bundled helper: `scripts/statsmodels_admission_logit.py`

## Bundled helper

```bash
python3 scripts/statsmodels_admission_logit.py \
  --train references/data/admissions_train.csv \
  --test references/data/admissions_test.csv \
  --output ./admissions_predictions.csv \
  --no-plots
```
