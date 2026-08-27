---
name: datasets
description: "Use Fairlearn built-in dataset loaders, schema notes, cache
  controls, and dataset fairness warnings."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Fairlearn datasets

Use this sub-skill when the task asks for Fairlearn built-in datasets, OpenML-backed loaders, dataset schemas, `fetch_adult`, `fetch_acs_income`, `fetch_bank_marketing`, `fetch_boston`, `fetch_credit_card`, `fetch_diabetes_hospital`, `as_frame`, `return_X_y`, `data_home`, `cache`, ACS state filtering, or `DataFairnessWarning`.

## Quick workflow

1. Decide whether the task needs a real dataset download or only loader/schema guidance.
2. Choose the smallest relevant loader and set `data_home` explicitly in restricted or reproducible environments.
3. Use `as_frame=True` for pandas DataFrames with dtypes and feature names; use `return_X_y=True` for direct `(X, y)` workflows.
4. Keep dataset fairness warnings visible, especially for Boston housing.
5. Route to `../assessment/` or a mitigation sub-skill after the dataset is loaded and preprocessed.

## Read these references

- [`references/dataset-loaders.md`](references/dataset-loaders.md) for loader signatures, dataset sizes, columns, return shapes, cache behavior, and loader-specific caveats.
- [`references/troubleshooting.md`](references/troubleshooting.md) for network/cache failures, ACS state-code errors, Boston warnings, and `as_frame`/`return_X_y` confusion.
- [`scripts/preview_dataset_loaders.py`](scripts/preview_dataset_loaders.py) for a no-network signature preview and optional single-loader download check.

## Core APIs to recognize

- `fetch_adult(*, cache=True, data_home=None, as_frame=True, return_X_y=False)`
- `fetch_acs_income(*, cache=True, data_home=None, as_frame=True, return_X_y=False, states=None)`
- `fetch_bank_marketing(*, cache=True, data_home=None, as_frame=True, return_X_y=False)`
- `fetch_boston(*, cache=True, data_home=None, as_frame=True, return_X_y=False, warn=True)`
- `fetch_credit_card(*, cache=True, data_home=None, as_frame=True, return_X_y=False)`
- `fetch_diabetes_hospital(*, as_frame=True, cache=True, data_home=None, return_X_y=False)`

## Boundary rules

- This sub-skill owns loader behavior and dataset caveats. It does not own model training, assessment metrics, or mitigation algorithms.
- Use `../assessment/` after obtaining predictions or scores.
- Use `../preprocessing/`, `../reductions/`, `../postprocessing/`, or `../adversarial/` for mitigation choices.
- Use `../installation/` if the issue is a package import rather than loader behavior.

## Operating rules

- Dataset loaders can perform network downloads. Ask before downloading when network, disk, or privacy constraints are unclear.
- Default cache location is a `.fairlearn-data` directory under the user's home unless `data_home` is set.
- Prefer `as_frame=True` for Fairlearn workflows because column names make sensitive-feature selection auditable.
- `fetch_boston(warn=True)` intentionally raises `DataFairnessWarning`; do not suppress it in reports unless the user explicitly asks and understands why.
- `fetch_acs_income(states=...)` expects two-letter state abbreviations; `PR` is accepted for Puerto Rico.

## Fast validation

No-network signature preview:

```bash
python sub-skills/datasets/scripts/preview_dataset_loaders.py
```

Optional single-loader download check:

```bash
python sub-skills/datasets/scripts/preview_dataset_loaders.py --download adult --data-home /tmp/fairlearn-data
```
