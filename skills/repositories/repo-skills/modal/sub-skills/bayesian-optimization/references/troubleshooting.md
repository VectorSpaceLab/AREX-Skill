# Bayesian Optimization Troubleshooting

## Purpose

Read this when a `BayesianOptimizer` workflow fails, loops too long, returns surprising indices, or reports unexpected `X_max`/`y_max` values.

## Failure modes and recoveries

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ValueError` from `teach()` about inconsistent dimensions or lengths. | `X` and `y` do not contain the same number of rows, or a single selected row was flattened incorrectly. | Keep candidates as 2-D rows: `query_inst = np.asarray(query_inst).reshape(k, -1)`. Normalize objective outputs to `np.asarray(y_new).reshape(k,)` or another consistent one-scalar-per-row shape before `teach()`. |
| `y_max` is an array with surprising nesting, or `get_max()` is hard to print/compare. | Initial or taught `y` values were supplied as nested column arrays such as `(n, 1)` and mixed with scalar/1-D results. | Prefer `y_training.shape == (n,)` and `y_new.shape == (k,)` for scalar objectives. Convert with `np.asarray(values, dtype=float).reshape(-1)`. |
| `get_max()` does not change after `teach()`. | The new observed value did not exceed the current observed maximum, the workflow is minimizing without negating the loss, or the wrong `y_new` was passed. | Check `X_new`, `y_new`, and `optimizer.get_max()` immediately before and after `teach()`. For minimization, teach `-loss` or another larger-is-better score. Remember that `get_max()` tracks observed `y`, not predicted means. |
| `TypeError: predict() got an unexpected keyword argument 'return_std'` or unpacking errors around `(mean, std)`. | The estimator does not implement the Gaussian-process-style `predict(X, return_std=True)` contract required by built-in acquisitions. | Use `GaussianProcessRegressor`, a compatible surrogate regressor, or a wrapper whose `predict(..., return_std=True)` returns two arrays. Do not use ordinary classifiers for acquisition functions. |
| Acquisition scores contain `NaN`, `inf`, or warnings from division by zero. | Predictive standard deviation is zero/near-zero for duplicate candidates, the model is overconfident at training points, or candidate features contain non-finite values. | Remove already evaluated rows from the candidate pool, validate `np.isfinite(X_pool).all()`, use a small GP `alpha` jitter, and inspect `std` from `optimizer.predict(X_pool, return_std=True)`. Avoid direct `PI`/`EI` calls with zero `std`. |
| `query_idx` is an array when only one row was requested. | modAL's max strategies return NumPy index arrays from `multi_argmax`, even for `n_instances=1`. | Normalize with `idx = np.asarray(query_idx).reshape(-1)`. Use these indices against the same `X_pool` object passed to `query()`. |
| The wrong candidate is removed from the pool after `query()`. | `query_idx` was treated as a global grid index, but it indexes the current pool passed to `optimizer.query()`. | If you need global IDs, maintain a parallel `candidate_ids` array and delete by the same pool-relative indices. |
| Objective cost explodes because every candidate is evaluated each loop. | The workflow copied a toy plotting example pattern instead of a real expensive-objective loop. | Query first, evaluate only `query_inst`, then call `teach()`. Full-grid objective evaluation is acceptable only for deterministic toy validation where the objective is intentionally cheap. |
| The same point is queried repeatedly. | Evaluated rows remain in the finite candidate pool, or duplicated rows exist. | Delete queried rows from `X_pool`, keep a visited set by candidate ID/tuple, and avoid duplicate design rows. For continuous query synthesis, add a custom duplicate guard before objective evaluation. |
| Results differ between PI/EI/UCB comparisons. | The strategies were not given identical initial observations, candidate pools, or budgets, or GP hyperparameter optimization introduced nondeterminism. | Reinitialize a fresh optimizer for each strategy with the same `X_training`/`y_training`, copy the same `X_pool`, set a fixed surrogate configuration when possible, and compare observed `get_max()` values after the same number of objective calls. |
| `on_transformed=True` does not affect acquisition behavior as expected. | Built-in acquisition functions call `optimizer.predict(X, return_std=True)` and do not perform acquisition-specific transformation logic. | If the estimator is a scikit-learn `Pipeline`, pass raw features to the pipeline and let `predict` transform internally. For custom transformed-pool strategies, route generic strategy design to the query-strategies sub-skill. |
| Long loops, plotting, or model refits are too slow. | Candidate pool is too large, budget is unbounded, GP fitting is expensive, or plotting code from examples was retained. | Set a small explicit `budget`, subsample or prefilter candidates, use a cheaper surrogate or fixed GP optimizer settings for smoke tests, disable plotting in runtime helpers, and stop when a score/time condition is met. |

## Quick diagnostic sequence

1. Run the bundled smoke script linked from the router. From this sub-skill directory, use `python scripts/bayesian_optimizer_smoke.py`; from any other working directory, pass Python the corresponding path to `scripts/bayesian_optimizer_smoke.py` in this generated skill tree.
2. Confirm `X_pool.ndim == 2` and `len(y_training) == len(X_training)`.
3. Check the estimator contract:
   ```python
   mean, std = optimizer.predict(X_pool[:3], return_std=True)
   ```
4. Inspect acquisition scores without evaluating the objective:
   ```python
   from modAL.acquisition import optimizer_EI
   scores = optimizer_EI(optimizer, X_pool)
   ```
5. Query one row, evaluate one scalar, teach it, and check `optimizer.get_max()`.

If the failure is about generic learner lifecycle, estimator fitting, or custom strategy combinators rather than optimizer-specific acquisition behavior, use the sibling learner or query-strategy sub-skills linked from the router.
