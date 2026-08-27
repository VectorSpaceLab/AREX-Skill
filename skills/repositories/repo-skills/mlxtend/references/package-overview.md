# mlxtend Package Overview

Read this when a task asks what mlxtend covers, which sub-skill to use, how to install/import it, or how its workflows connect. For deep API details, follow the nearest sub-skill route from the root `SKILL.md`.

## Scope

mlxtend (machine learning extensions) is a Python package of sklearn-adjacent utilities for day-to-day data science tasks. This skill covers version-era behavior for package `mlxtend` with import name `mlxtend`.

Primary user-facing areas:

| Area | Owning route | Typical tasks |
|---|---|---|
| Estimators and ensembles | `sub-skills/estimators-and-ensembles/SKILL.md` | Voting/stacking classifiers, stacking regressors, classic educational estimators, Kmeans, sklearn grid-search parameter routing. |
| Evaluation and validation | `sub-skills/evaluation-and-validation/SKILL.md` | Accuracy/scoring/confusion/lift, bootstrap/OOB/.632, permutation tests, paired model-comparison tests, McNemar/Cochran/F tests, holdout and grouped time-series splitters, feature importance, counterfactuals. |
| Feature workflows | `sub-skills/feature-workflows/SKILL.md` | Sequential/exhaustive feature selection, column selection, PCA/LDA/RBF kernel PCA, scaling/standardizing, dense conversion, one-hot labels, transaction encoding. |
| Frequent patterns | `sub-skills/frequent-patterns/SKILL.md` | Transaction encoding handoff, apriori/fpgrowth/fpmax/hmine itemsets, association rules, rule metrics and threshold tuning. |
| Plotting and utilities | `sub-skills/plotting-and-utilities/SKILL.md` | Matplotlib plots, headless figures, packaged datasets, file grouping, text/name helpers, combinatorics/vector helpers, small utility checks. |

## Install and import

Use a normal Python environment with Python 3.11 or newer for this snapshot's package metadata.

```bash
python -m pip install mlxtend
python - <<'PY'
import mlxtend
print(mlxtend.__version__)
from mlxtend.classifier import EnsembleVoteClassifier
from mlxtend.frequent_patterns import apriori
print("mlxtend import ok")
PY
```

For a uv-managed project:

```bash
uv add mlxtend
```

Runtime dependencies declared by this snapshot include NumPy, SciPy, pandas, scikit-learn, Matplotlib, and joblib. The package does not expose a first-class command-line interface; use Python APIs and the bundled smoke scripts.

Optional groups observed in package metadata:

- `testing`: pytest/coverage for running package tests or this skill's deeper checks.
- `docs`: documentation build dependencies; not needed for normal package use.

## Minimal environment check

From the root generated skill directory, run:

```bash
python scripts/check_mlxtend_env.py
```

For a deeper self-contained smoke across every sub-skill:

```bash
MPLBACKEND=Agg python scripts/check_mlxtend_env.py --run-subskill-smokes
```

The deeper check runs the bundled sub-skill scripts only. It does not require the original repository files.

## Workflow map

- Estimator workflow: choose/fetch data (`plotting-and-utilities` for toy data), build/fill estimator (`estimators-and-ensembles`), evaluate/statistically compare (`evaluation-and-validation`), then visualize (`plotting-and-utilities`).
- Feature workflow: transform/select features (`feature-workflows`), train/evaluate downstream model (`estimators-and-ensembles` and `evaluation-and-validation`), then plot SFS/PCA/decision diagnostics (`plotting-and-utilities`).
- Transaction workflow: encode list-of-lists transactions (`feature-workflows`), mine itemsets and rules (`frequent-patterns`), then optionally plot or export results with normal pandas/Matplotlib utilities.

## No selected accelerator or service backend

All selected mlxtend workflows are CPU Python APIs. A GPU may be visible on a host, but mlxtend's public APIs here do not require CUDA, ROCm, MPS, external services, credentials, model downloads, or long training jobs.

## Refresh hints

Read `repo-provenance.md` before deciding whether this skill is current for a different checkout. Refresh when the package version, public module layout, dependency floors, or major behavior in tests/docs changes.
