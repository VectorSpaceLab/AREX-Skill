# Acquisition and API Reference

## Purpose

Read this reference when selecting or debugging modAL's Bayesian optimization APIs: `BayesianOptimizer`, raw acquisition utilities (`PI`, `EI`, `UCB`), optimizer score functions (`optimizer_PI`, `optimizer_EI`, `optimizer_UCB`), and max-query strategies (`max_PI`, `max_EI`, `max_UCB`).

## `BayesianOptimizer` surface

| API | Use | Important behavior |
|---|---|---|
| `BayesianOptimizer(estimator, query_strategy=max_EI, X_training=None, y_training=None, bootstrap_init=False, on_transformed=False, **fit_kwargs)` | Initialize an optimizer around a scalar regressor. | If `X_training` is provided, the estimator is fit immediately. If `y_training` is provided, the optimizer initializes `X_max` and `y_max` from the best observed training value. |
| `query(X_pool, *args, return_metrics=False, **kwargs)` | Choose candidate rows from a finite pool. | With built-in max acquisitions, returns `(query_idx, query_instances)` by default. `query_idx` indexes rows in the pool passed to this call. With `return_metrics=True`, returns `(query_idx, query_instances, metrics)` when the strategy provides acquisition scores. |
| `teach(X, y, bootstrap=False, only_new=False, **fit_kwargs)` | Add newly evaluated objective values and refit the estimator. | Adds `X`/`y` to stored training data, refits, then updates `X_max`/`y_max` from the newly supplied `y` if it improves the observed maximum. |
| `get_max()` | Read the best observed point/value. | Returns `(X_max, y_max)`. This is based on evaluated training data, not on predicted acquisition scores over the unevaluated pool. |
| `predict(X, return_std=True)` | Delegate to the wrapped estimator. | Built-in acquisition score functions require the estimator to accept `return_std=True` and return `(mean, std)`. |

`BayesianOptimizer` is a sibling of `ActiveLearner` and inherits much of the learner lifecycle. Use this sub-skill for optimizer-specific behavior; route generic learner lifecycle questions to the learners/committees sub-skill.

## Estimator contract

The practical estimator contract for built-in acquisition strategies is:

```python
mean, std = estimator.predict(X_candidates, return_std=True)
```

`GaussianProcessRegressor` satisfies this contract. A regressor that only returns point predictions will fail when used with `optimizer_PI`, `optimizer_EI`, `optimizer_UCB`, `max_PI`, `max_EI`, or `max_UCB`. A classifier may technically accept numeric labels, but Bayesian optimization acquisition values are meaningful for scalar regression, not classification labels.

## Raw acquisition utilities

| Function | Formula intent | Signature facts | When to call directly |
|---|---|---|---|
| `PI(mean, std, max_val, tradeoff)` | Probability that a candidate improves over the observed maximum by at least `tradeoff`. | Accepts arrays for `mean` and `std`, current best `max_val`, and scalar `tradeoff`. | Rarely needed; use `optimizer_PI` unless you already computed mean/std yourself. |
| `EI(mean, std, max_val, tradeoff)` | Expected improvement over the observed maximum after subtracting `tradeoff`. | Uses Gaussian CDF/PDF; `std` must be positive and finite. | Useful for custom diagnostics or tests with precomputed mean/std. |
| `UCB(mean, std, beta)` | Upper confidence bound `mean + beta * std`. | `beta` controls exploration weight. | Useful for custom scoring with precomputed mean/std. |

These raw utilities do not query the estimator and do not update the optimizer.

## Optimizer score functions

| Function | Default parameter | Returns | Notes |
|---|---:|---|---|
| `optimizer_PI(optimizer, X, tradeoff=0)` | `tradeoff=0` | PI utility for every row in `X`. | Uses `optimizer.predict(X, return_std=True)` and `optimizer.y_max`. |
| `optimizer_EI(optimizer, X, tradeoff=0)` | `tradeoff=0` | EI utility for every row in `X`. | Default score behind `max_EI`. |
| `optimizer_UCB(optimizer, X, beta=1)` | `beta=1` | UCB utility for every row in `X`. | Does not use `optimizer.y_max`. |

Implementation details that matter for debugging:

- Fitted estimators have `mean` and `std` reshaped to one-dimensional arrays before scoring.
- If the estimator raises `NotFittedError`, the score functions fall back to zero mean and unit standard deviation arrays. In production workflows, prefer seeding with real `X_training`/`y_training` so acquisition scores come from a fitted model.
- `PI` and `EI` use `optimizer.y_max`; if `y_max` has an awkward shape because labels were supplied as nested arrays, normalize future `y` values to one scalar per row and inspect `get_max()`.

## Max-query strategies

| Query strategy | Signature | Selects by | Exploration parameter |
|---|---|---|---|
| `max_PI(optimizer, X, tradeoff=0, n_instances=1)` | Returns `(indices, pi_values)` when called directly. | Largest `optimizer_PI` scores. | Larger `tradeoff` asks for more improvement before PI is high. |
| `max_EI(optimizer, X, tradeoff=0, n_instances=1)` | Returns `(indices, ei_values)` when called directly. | Largest `optimizer_EI` scores. | Larger `tradeoff` makes improvement harder and can shift search toward uncertain regions. |
| `max_UCB(optimizer, X, beta=1, n_instances=1)` | Returns `(indices, ucb_values)` when called directly. | Largest `optimizer_UCB` scores. | Larger `beta` favors high-uncertainty candidates. |

When these are assigned as `query_strategy`, call them through `optimizer.query(X_pool)`. The learner wrapper returns row indices and selected rows; if you need metrics, pass `return_metrics=True`.

For all three strategies, `n_instances` must be no larger than the candidate-pool length. Indices are usually NumPy arrays even when `n_instances=1`, so normalize with `np.asarray(query_idx).reshape(-1)` before using them in bookkeeping.

## Choosing an acquisition

- Start with `max_EI` for balanced exploitation/exploration and compatibility with modAL's default `BayesianOptimizer` query strategy.
- Use `max_PI` when the goal is a high probability of beating the current best by at least a chosen margin. It can be greedier than EI when `tradeoff` is small.
- Use `max_UCB` when you want an explicit knob (`beta`) for uncertainty-driven exploration.
- Compare strategies under the same initial observations, candidate pool, and evaluation budget. Report observed `get_max()` values, not acquisition scores alone.

## Return-shape examples

```python
query_idx, query_inst = optimizer.query(X_pool)
# query_idx: array-like row indices into X_pool, e.g. array([17])
# query_inst: selected rows from X_pool, e.g. shape (1, n_features)

query_idx, query_inst, metric = optimizer.query(X_pool, return_metrics=True)
# metric: acquisition utility score(s) returned by max_PI/max_EI/max_UCB for selected row(s)

scores = optimizer_EI(optimizer, X_pool, tradeoff=0.05)
# scores: one utility per row in X_pool; reshape to (-1,) for plotting or argmax diagnostics.
```

## Evidence distilled

The API facts in this reference were verified from installed signatures, the `BayesianOptimizer` source, the acquisition source, the model/acquisition documentation, and repository tests covering acquisition utilities, query selection, `X_max`/`y_max`, `teach()`, `get_max()`, and `on_transformed` construction.
