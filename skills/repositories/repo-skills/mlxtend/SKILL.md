---
name: mlxtend
description: "Use mlxtend machine-learning extension utilities for estimator
  ensembles, evaluation, feature workflows, frequent patterns, plotting,
  datasets, and small helper APIs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# mlxtend

Use this repo skill when a task needs package-specific guidance for mlxtend (machine learning extensions): sklearn-style ensemble/meta-estimators, evaluation and model-comparison utilities, feature selection/extraction/preprocessing, frequent itemset and association-rule mining, Matplotlib diagnostics, packaged toy data, file/text/math helpers, or troubleshooting for those APIs.

## Start here

1. Read [references/package-overview.md](references/package-overview.md) for package scope, install/import checks, dependency notes, and cross-workflow routing.
2. Read [references/troubleshooting.md](references/troubleshooting.md) for install/import, dependency, headless Matplotlib, sklearn compatibility, shape, slow-workflow, and file-group issues.
3. Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill is current for a different mlxtend checkout or package version.
4. Run [scripts/check_mlxtend_env.py](scripts/check_mlxtend_env.py) when you need to verify imports and, optionally, all bundled sub-skill smoke workflows.

## Install and quick check

```bash
python -m pip install mlxtend
python - <<'PY'
import mlxtend
print(mlxtend.__version__)
from mlxtend.evaluate import accuracy_score
from mlxtend.frequent_patterns import apriori
print("mlxtend import ok")
PY
```

mlxtend is a Python API package; no first-class mlxtend CLI entry point is expected. For a deeper generated-skill check, run:

```bash
MPLBACKEND=Agg python scripts/check_mlxtend_env.py --run-subskill-smokes
```

## Sub-skill routes

| If the task asks about... | Read |
|---|---|
| Voting classifiers, stacking classifiers/regressors, classic mlxtend estimators, Kmeans, sklearn `GridSearchCV` parameter prefixes, `predict_proba`, sample weights, convergence, fit/predict behavior | [sub-skills/estimators-and-ensembles/SKILL.md](sub-skills/estimators-and-ensembles/SKILL.md) |
| Accuracy/scoring/confusion/lift, bootstrap/OOB/.632, permutation tests, paired t-tests, 5x2cv F tests, McNemar/Cochran tests, holdout splitters, grouped time-series splitters, feature importance, counterfactuals | [sub-skills/evaluation-and-validation/SKILL.md](sub-skills/evaluation-and-validation/SKILL.md) |
| `SequentialFeatureSelector`, `ExhaustiveFeatureSelector`, `ColumnSelector`, PCA/LDA/RBF kernel PCA, scaling/standardization, sparse/dense transforms, one-hot labels, `TransactionEncoder` preprocessing | [sub-skills/feature-workflows/SKILL.md](sub-skills/feature-workflows/SKILL.md) |
| `apriori`, `fpgrowth`, `fpmax`, `hmine`, `association_rules`, transaction-to-one-hot schemas, rule metrics, empty itemset/rule diagnosis, large itemset memory choices | [sub-skills/frequent-patterns/SKILL.md](sub-skills/frequent-patterns/SKILL.md) |
| `plot_decision_regions`, confusion-matrix/heatmap/learning-curve/SFS/PCA/scatter plots, headless Matplotlib, packaged datasets, `find_files`, `find_filegroups`, tokenizers, name helpers, math and utils | [sub-skills/plotting-and-utilities/SKILL.md](sub-skills/plotting-and-utilities/SKILL.md) |

## Common route combinations

- Estimator analysis: use `estimators-and-ensembles` to build/fix the model, `evaluation-and-validation` to score or compare it, and `plotting-and-utilities` to visualize decision regions, confusion matrices, or learning curves.
- Feature engineering: use `feature-workflows` for selectors/transforms, then route to `estimators-and-ensembles` or `evaluation-and-validation` for downstream model checks.
- Market-basket mining: use `feature-workflows` for `TransactionEncoder` details when needed, then use `frequent-patterns` for itemsets/rules and threshold troubleshooting.
- Headless examples or CI checks: set `MPLBACKEND=Agg`, run the nearest sub-skill smoke script, and close/save Matplotlib figures rather than displaying them.

## Boundaries

- Do not use this skill for generic scikit-learn, pandas, NumPy, or Matplotlib tasks unless the user specifically needs an mlxtend API, example, failure mode, or compatibility detail.
- Do not use this skill for deep-learning training/serving, LLM workflows, distributed compute, experiment tracking, or repository-maintenance tasks unrelated to mlxtend's public package APIs.
- All selected workflows are CPU Python APIs. No CUDA, ROCm, MPS, external service, credential, or model-download backend is required by this generated skill.
