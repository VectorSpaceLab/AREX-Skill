# API Reference

## Purpose

Use this reference when you need verified signatures, class responsibilities, and the differences between the built-in search algorithms. It is intentionally compact; longer examples live in `workflows.md`.

## Core objects

| Object | Verified signature | What it does |
| --- | --- | --- |
| `HyperParameters` | `HyperParameters()` | Owns the search space and the current active values. Methods include `Choice`, `Int`, `Float`, `Boolean`, `Fixed`, `conditional_scope`, `name_scope`, `copy`, `merge`, `get`, `to_proto`, and `from_proto`. |
| `HyperModel` | `HyperModel(name=None, tunable=True)` | Defines `build(hp)` and optionally `fit(hp, model, *args, **kwargs)` or `declare_hyperparameters(hp)`. |
| `Objective` | `Objective(name, direction)` | Names the metric and the optimization direction. Strings are also accepted by most constructors. |
| `Oracle` | `Oracle(objective=None, max_trials=None, hyperparameters=None, allow_new_entries=True, tune_new_entries=True, seed=None, max_retries_per_trial=0, max_consecutive_failed_trials=3)` | Chooses the next trial values and tracks search state. |
| `Trial` | `Trial(hyperparameters, trial_id=None, status='RUNNING', message=None)` | Stores one candidate configuration, its metrics, status, and error message. |
| `BaseTuner` | `BaseTuner(oracle, hypermodel=None, directory=None, project_name=None, overwrite=False, **kwargs)` | Owns the search loop, trial persistence, and best-model loading for non-Keras or custom tuners. |
| `Tuner` | `Tuner(oracle, hypermodel=None, max_model_size=None, optimizer=None, loss=None, metrics=None, distribution_strategy=None, directory=None, project_name=None, logger=None, tuner_id=None, overwrite=False, executions_per_trial=1, **kwargs)` | The Keras-model-aware base tuner. |

## HyperParameters behavior

- `Choice(name, values, ordered=None, default=None, parent_name=None, parent_values=None)` selects one value from a finite list.
- `Int(name, min_value, max_value, step=None, sampling='linear', default=None, parent_name=None, parent_values=None)` includes the upper bound.
- `Float(name, min_value, max_value, step=None, sampling='linear', default=None, parent_name=None, parent_values=None)` supports linear, log, and reverse-log sampling.
- `Boolean(name, default=False, parent_name=None, parent_values=None)` is a specialized choice.
- `Fixed(name, value, parent_name=None, parent_values=None)` registers a non-tunable value.
- `conditional_scope(parent_name, parent_values)` gates children on the parent value.
- `name_scope(name)` prefixes nested names with slash-separated scopes.
- `values` contains only active values; inactive values are intentionally hidden.
- `copy()` and `merge()` preserve search-space structure and active values.

## Built-in tuning algorithms

| Class | Verified signature | Notes |
| --- | --- | --- |
| `RandomSearch` | `RandomSearch(hypermodel=None, objective=None, max_trials=10, seed=None, hyperparameters=None, tune_new_entries=True, allow_new_entries=True, max_retries_per_trial=0, max_consecutive_failed_trials=3, **kwargs)` | Randomly samples the search space until the oracle stops. |
| `GridSearch` | `GridSearch(hypermodel=None, objective=None, max_trials=None, seed=None, hyperparameters=None, tune_new_entries=True, allow_new_entries=True, max_retries_per_trial=0, max_consecutive_failed_trials=3, **kwargs)` | Exhaustively enumerates finite choice spaces; float/int spaces without an explicit `step` are sampled at 10 points. |
| `Hyperband` | `Hyperband(hypermodel=None, objective=None, max_epochs=100, factor=3, hyperband_iterations=1, seed=None, hyperparameters=None, tune_new_entries=True, allow_new_entries=True, max_retries_per_trial=0, max_consecutive_failed_trials=3, **kwargs)` | Adds special `tuner/trial_id`, `tuner/initial_epoch`, and `tuner/epochs` hyperparameters during successive halving. `factor` must be at least 2. |
| `BayesianOptimization` | `BayesianOptimization(hypermodel=None, objective=None, max_trials=10, num_initial_points=None, alpha=0.0001, beta=2.6, seed=None, hyperparameters=None, tune_new_entries=True, allow_new_entries=True, max_retries_per_trial=0, max_consecutive_failed_trials=3, **kwargs)` | Uses a Gaussian-process search. It requires both SciPy and scikit-learn at construction time. |

### Search and result methods

- `search(*fit_args, **fit_kwargs)` runs the search loop.
- `get_best_models(num_models=1)` reloads the top trials' saved models.
- `get_best_hyperparameters(num_trials=1)` returns the top trial hyperparameter objects.
- `search_space_summary(extended=False)` prints the discovered search space.
- `results_summary(num_trials=10)` prints the best trials and metrics.
- `save()` and `reload()` persist and restore tuner state from `directory/project_name`.
- `project_dir` and `get_trial_dir(trial_id)` expose the on-disk layout.

## Sklearn tuning

`SklearnTuner` is the estimator-oriented adapter:

- Signature: `SklearnTuner(oracle, hypermodel, scoring=None, metrics=None, cv=None, **kwargs)`.
- `search(X, y, sample_weight=None, groups=None)` runs cross-validated search.
- `X` and `y` may be `numpy.ndarray` or `pandas.DataFrame`.
- `save_model` stores a pickled estimator, and `load_model` restores it.
- If the estimator fit method does not accept `sample_weight`, the tuner omits it.

## Image hypermodels

| Class | Verified signature | Notes |
| --- | --- | --- |
| `HyperResNet` | `HyperResNet(include_top=True, input_shape=None, input_tensor=None, classes=None, **kwargs)` | Builds a tunable ResNet-style image classifier. `classes` is required when `include_top=True`. |
| `HyperXception` | `HyperXception(include_top=True, input_shape=None, input_tensor=None, classes=None, **kwargs)` | Builds a tunable Xception-style image classifier. `classes` is required when `include_top=True`. |
| `HyperEfficientNet` | `HyperEfficientNet(input_shape=None, input_tensor=None, classes=None, augmentation_model=None, **kwargs)` | Builds on Keras Applications EfficientNet backbones and can use a fixed or tunable augmentation model. The first build may fetch pretrained weights. |
| `HyperImageAugment` | `HyperImageAugment(input_shape=None, input_tensor=None, rotate=0.5, translate_x=0.4, translate_y=0.4, contrast=0.3, augment_layers=3, **kwargs)` | Tunes image augmentation layers and ranges. `augment_layers=0` means fixed sequential transforms; nonzero enables RandAugment-style search. |

## Distributed tuning

- `OracleClient` wraps RPC calls to the chief server.
- `OracleServicer` exposes the server-side gRPC methods.
- `config.backend()` reports the active backend, and `config.multi_backend()` indicates whether Keras 3 style multi-backend mode is active.

Read the workflow and troubleshooting references for example call sequences and common failure modes.
