---
name: kaggle-linear-models
description: "Safe, modern Kaggle-style SVM and logistic-regression workflows
  for dense matrices, hashed sparse CSVs, and one-hot categorical tables."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Kaggle Linear Models

Use this sub-skill for classical tabular machine-learning tasks that look like Kaggle starter code and should stay bounded, reproducible, and Python 3 friendly.

## Choose a route

- Dense numeric matrix plus class labels: use `scripts/sklearn_svm_submission.py`.
- Criteo-like sparse CSV with `Label` and `Id` columns: use `scripts/hashed_logistic_sgd.py`.
- Categorical table with `ACTION`/`id` columns: use `scripts/categorical_logistic_submission.py`.
- Synthetic smoke fixtures for all helpers: use `scripts/make_tiny_fixtures.py`.

Read `references/workflows.md` for runnable recipes, `references/data-formats.md` when the CSV layout is unclear, `references/api-reference.md` for current scikit-learn usage, and `references/troubleshooting.md` when a run fails.

## What this sub-skill includes

- Dense-matrix SVC submissions with configurable SVC arguments.
- Hashed online logistic regression for Criteo-like sparse categorical CSVs.
- One-hot categorical logistic regression with optional bounded cross-validation.
- Interaction-feature guidance from the expanded Amazon-style logistic example, kept reference-only unless the user explicitly asks for a bounded experiment.

## What stays out

- Admissions logistic regression with statsmodels. That route is owned by `statsmodels-logit-workflow`.
- Live Twitter/X ingestion or JSON streaming. That route is owned by `twitter-json-workflow`.
- Exhaustive greedy feature selection over a large feature lattice.
- Any workflow that depends on the original repository checkout.

If a user asks for one of those excluded routes, point them to the sibling skill that owns that route instead of extending this one.

## Quick selection rules

1. If the input is a dense numeric matrix with a separate label file, start with `sklearn_svm_submission.py`.
2. If the input is a sparse tabular CSV with `Label`/`Id` columns and mixed string or numeric feature values, start with `hashed_logistic_sgd.py`.
3. If the input is a categorical CSV with `ACTION`/`id` columns, start with `categorical_logistic_submission.py`.
4. If you need tiny fixtures to smoke-test the helpers, generate them first with `make_tiny_fixtures.py`.

## Expected behavior

- All bundled scripts accept explicit paths and `--help`.
- The helpers create missing parent directories for outputs.
- The modernized categorical workflow uses `OneHotEncoder(handle_unknown="ignore", sparse_output=True)`.
- The categorical workflow uses bounded `StratifiedKFold` cross-validation only when you request it.
- The interaction-feature recipe is documentation only by default; it should not be promoted into a default script unless the user gives a small dataset and a clear budget.

## When to read each bundled reference

- `references/workflows.md`: end-to-end command recipes and the reference-only interaction-feature pattern.
- `references/data-formats.md`: required columns, label conventions, and output layouts.
- `references/api-reference.md`: current sklearn signatures and API replacements for removed legacy names.
- `references/troubleshooting.md`: old sklearn API errors, unseen categories, single-class folds, large feature spaces, and the broken v2 hashed script.

## When to run each bundled helper

- `scripts/make_tiny_fixtures.py`: create small dense, hashed, and categorical fixtures for smoke tests.
- `scripts/sklearn_svm_submission.py`: fit an SVC on dense numeric matrices and write class predictions.
- `scripts/hashed_logistic_sgd.py`: fit an online hashed logistic model on Criteo-like CSVs and write probabilities.
- `scripts/categorical_logistic_submission.py`: fit a modern sparse one-hot logistic model on categorical CSVs and optionally report bounded CV AUC.
