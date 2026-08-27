---
name: learners-and-committees
description: "Router for ActiveLearner, Committee, and CommitteeRegressor workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# learners-and-committees

Use this sub-skill for:
- `ActiveLearner` workflows for pool-based and stream-based active learning.
- `Committee` workflows for query by committee, voting, class/proba reconciliation, and bagging.
- `CommitteeRegressor` workflows for ensemble regression and standard-deviation query selection.

Keep the task here when it is about learner lifecycle, single-row teach/query shape handling, bagging, or committee disagreement. If the task is mainly about query-strategy formulas, selectors, or combinators, route to [../query-strategies/SKILL.md](../query-strategies/SKILL.md). If it is Bayesian optimization or deep/skorch/Keras/PyTorch, route elsewhere.

## Read first
- [references/workflows.md](references/workflows.md) — initialization, query/teach/fit loops, stream sampling, committee bagging, and regression recipes.
- [references/api-reference.md](references/api-reference.md) — signatures, return shapes, estimator requirements, and single-row handling.
- [references/troubleshooting.md](references/troubleshooting.md) — recovery notes for shape mismatches, unfitted estimators, missing `predict_proba`, `on_transformed`, `return_metrics`, and `only_new`.

## Run
- [scripts/active_learning_smoke.py](scripts/active_learning_smoke.py) — deterministic pool, stream, `bootstrap_init`, `bootstrap`, `only_new`, `fit`, `return_metrics`, and `on_transformed` smoke.
- [scripts/committee_smoke.py](scripts/committee_smoke.py) — deterministic committee vote/proba alignment, `rebag`, bagging, and `CommitteeRegressor` standard-deviation smoke.

## Route elsewhere
- Query-strategy formulas, selectors, or combinators: [../query-strategies/SKILL.md](../query-strategies/SKILL.md)
- BayesianOptimizer and acquisition loops: [../bayesian-optimization/SKILL.md](../bayesian-optimization/SKILL.md)
- DeepActiveLearner, skorch, Keras, PyTorch, or dropout helpers: [../deep-and-optional-integrations/SKILL.md](../deep-and-optional-integrations/SKILL.md)

## Quick rules
- Use an estimator with `fit` and `predict`; add `predict_proba` when the strategy needs probabilities.
- Teach/query single rows with the same shape style as the original training data. For NumPy, reshape single samples with `(1, -1)` and labels with `(1,)`.
- `bootstrap_init=True` bootstraps the first fit; `teach(..., bootstrap=True)` bootstraps the refit; `rebag()` refits each learner on a bootstrap sample of its own history.
- `only_new=True` fits only the fresh batch and does not append it to stored training history.
- `Committee` reconciles class labels across learners; `CommitteeRegressor` uses ensemble prediction standard deviation instead of class probabilities.
- There is no public `bag()` method in this release; use the bootstrap flags and `rebag()` instead.
