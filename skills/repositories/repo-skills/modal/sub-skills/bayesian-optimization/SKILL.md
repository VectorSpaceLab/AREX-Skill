---
name: bayesian-optimization
description: "Guides modAL BayesianOptimizer and PI/EI/UCB acquisition workflows
  for expensive scalar-function optimization with GP-style regressors."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Bayesian Optimization

Use this sub-skill when a task asks for Bayesian optimization with modAL: build a `BayesianOptimizer`, choose PI/EI/UCB acquisition behavior, run a bounded objective-evaluation loop, inspect acquisition scores, or debug `get_max()`/`y_max` tracking.

## Read or run first

- Read [references/workflows.md](references/workflows.md) when you need an end-to-end optimizer loop, shape conventions, 1-D or multidimensional candidate grids, or evaluation-budget guidance.
- Read [references/acquisition-reference.md](references/acquisition-reference.md) when choosing among `max_PI`, `max_EI`, `max_UCB` or inspecting `optimizer_PI`, `optimizer_EI`, `optimizer_UCB` score arrays.
- Read [references/troubleshooting.md](references/troubleshooting.md) when `teach`, `query`, acquisition utilities, `predict(return_std=True)`, or `get_max()` behave unexpectedly.
- Run [scripts/bayesian_optimizer_smoke.py](scripts/bayesian_optimizer_smoke.py) to check that the installed `modAL` package can execute a deterministic Bayesian optimization loop and print `PASS` with `get_max()` results.

## Route boundaries

- For general `ActiveLearner`, `Committee`, `query`, `teach`, `fit`, `return_metrics`, bagging, or estimator lifecycle questions, route to [../learners-and-committees/SKILL.md](../learners-and-committees/SKILL.md).
- For generic query strategy selection, custom strategy combinators, uncertainty/disagreement sampling, ranked batch, density, expected-error, or multilabel strategies, route to [../query-strategies/SKILL.md](../query-strategies/SKILL.md).
- Keep this sub-skill focused on scalar-objective maximization with regressors that can provide both predictive mean and predictive standard deviation.

## Minimal operating checklist

1. Define a finite candidate pool `X_pool` with shape `(n_candidates, n_features)`.
2. Seed `BayesianOptimizer` with at least one evaluated point: `X_training` has matching feature columns and `y_training` contains numeric scalar objective values.
3. Use a regressor whose `predict(X, return_std=True)` returns `(mean, std)`; `GaussianProcessRegressor` is the usual modAL-backed choice.
4. Query before evaluating the expensive objective: `query_idx, query_inst = optimizer.query(X_pool)`.
5. Evaluate only `query_inst`, normalize the result to one scalar per queried row, and call `optimizer.teach(query_inst, y_new)`.
6. Call `optimizer.get_max()` for the best observed location/value so far; do not recompute the maximum from unevaluated candidate predictions.
