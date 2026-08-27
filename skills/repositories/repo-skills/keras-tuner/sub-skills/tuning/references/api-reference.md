# Tuning API Reference

## Purpose

Use this when you need the exact tuning-oriented signatures and the behavior that differs among the built-in search algorithms.

## High-value signatures

- `HyperParameters()`
- `HyperModel(name=None, tunable=True)`
- `BaseTuner(oracle, hypermodel=None, directory=None, project_name=None, overwrite=False, **kwargs)`
- `Tuner(oracle, hypermodel=None, max_model_size=None, optimizer=None, loss=None, metrics=None, distribution_strategy=None, directory=None, project_name=None, logger=None, tuner_id=None, overwrite=False, executions_per_trial=1, **kwargs)`
- `RandomSearch(hypermodel=None, objective=None, max_trials=10, seed=None, hyperparameters=None, tune_new_entries=True, allow_new_entries=True, max_retries_per_trial=0, max_consecutive_failed_trials=3, **kwargs)`
- `GridSearch(hypermodel=None, objective=None, max_trials=None, seed=None, hyperparameters=None, tune_new_entries=True, allow_new_entries=True, max_retries_per_trial=0, max_consecutive_failed_trials=3, **kwargs)`
- `Hyperband(hypermodel=None, objective=None, max_epochs=100, factor=3, hyperband_iterations=1, seed=None, hyperparameters=None, tune_new_entries=True, allow_new_entries=True, max_retries_per_trial=0, max_consecutive_failed_trials=3, **kwargs)`
- `BayesianOptimization(hypermodel=None, objective=None, max_trials=10, num_initial_points=None, alpha=0.0001, beta=2.6, seed=None, hyperparameters=None, tune_new_entries=True, allow_new_entries=True, max_retries_per_trial=0, max_consecutive_failed_trials=3, **kwargs)`

## Important method contracts

- `HyperModel.build(hp)` must return a Keras model when used with `Tuner`.
- `HyperModel.fit(hp, model, *args, **kwargs)` may return the same shapes as `model.fit()` or a custom objective value.
- `Tuner.run_trial(trial, *args, **kwargs)` may return a `History`, float, dict, or list of those.
- `Tuner.save_model(trial_id, model, step=0)` and `load_model(trial)` must be implemented for custom model persistence.
- `search_space_summary()` and `results_summary()` are print helpers; they do not mutate state.
- `get_best_models(num_models=1)` uses the saved trial artifacts from the search directory.
- `get_best_hyperparameters(num_trials=1)` returns the top hyperparameter objects in best-trial order.

## Algorithm-specific notes

### RandomSearch

- Samples the space randomly.
- Good baseline when you want fast feedback and minimal tuning logic.

### GridSearch

- Walks the search space deterministically.
- Works best for finite `Choice` spaces or `Int`/`Float` spaces with explicit `step` values.
- `Float` and log-sampled `Int` spaces without a `step` use 10 samples.

### Hyperband

- Uses successive halving across brackets and rounds.
- Requires `factor >= 2`.
- Injects `tuner/trial_id`, `tuner/initial_epoch`, and `tuner/epochs` into later rounds.

### BayesianOptimization

- Fits a Gaussian process to completed trials.
- Requires SciPy and scikit-learn when you construct the tuner.
- Default `num_initial_points` is `3 * number_of_dimensions` when unspecified.

## TensorFlow trial dependency

The verified TensorFlow-backed 1.4.8 path imports
`tensorboard.plugins.hparams` while preparing Keras trials. Install
`tensorboard` alongside TensorFlow even if the caller does not explicitly add
a TensorBoard callback.

## HyperParameters details

- Active values live in `hp.values`.
- Inactive conditional values are intentionally hidden.
- `conditional_scope(parent_name, parent_values)` controls whether nested parameters become active.
- `name_scope(name)` prefixes nested names with slash-separated scopes.
- `copy()` and `merge()` preserve the search-space structure.

Read `references/workflows.md` for the actual user-facing search patterns.
