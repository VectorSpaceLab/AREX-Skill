# Collections and Wrappers API

## `MetricCollection`

Use `MetricCollection` when several metrics share the same call signature and should be updated, computed, cloned, or reset together.

Key constructor arguments:

| Argument | Meaning |
| --- | --- |
| `metrics` | A metric, list/tuple of metrics, dict of named metrics, or nested compatible collection. |
| `prefix` | String prepended to output keys. |
| `postfix` | String appended to output keys. |
| `compute_groups` | `True`, `False`, or explicit groups that let compatible metrics share state for faster updates. |

Important behavior:

- A dict gives stable explicit output names.
- A list uses metric class names and cannot disambiguate duplicate classes.
- `clone(prefix=..., postfix=...)` is the usual way to create train/validation/test metric groups with independent state.
- `update()` passes arguments to each metric and filters keyword arguments by member signature.
- `compute()` returns a dictionary keyed by prefix/postfix-adjusted metric names.

## Aggregation metrics

Aggregation helpers still follow the normal `Metric` lifecycle.

| Metric | Use |
| --- | --- |
| `MeanMetric` | Running mean of scalar or tensor values. |
| `SumMetric` | Running sum. |
| `MinMetric` / `MaxMetric` | Track extrema. |
| `CatMetric` | Concatenate values across updates. |
| `RunningMean` / `RunningSum` | Windowed running aggregation. |

## Wrappers

| Wrapper | Constructor pattern | Main use | Output caution |
| --- | --- | --- | --- |
| `ClasswiseWrapper` | `ClasswiseWrapper(metric, labels=None, prefix=None, postfix=None)` | Convert a per-class tensor metric into a dict of named class results. | Requires the base metric to return a first-dimension class vector. |
| `BootStrapper` | `BootStrapper(base_metric, num_bootstraps=10, mean=True, std=True, quantile=None, raw=False, sampling_strategy='poisson')` | Estimate mean/std/quantile uncertainty by bootstrap resampling. | Returns a dict; not always scalar-loggable without flattening. |
| `MinMaxMetric` | `MinMaxMetric(base_metric)` | Track raw, min, and max of a scalar base metric across computes. | Base result must be a scalar tensor or float. |
| `MultioutputWrapper` | `MultioutputWrapper(base_metric, num_outputs, output_dim=-1, remove_nans=True, squeeze_outputs=True)` | Apply a base metric independently over multiple output dimensions. | Output can be vector or nested structure. |
| `MultitaskWrapper` | `MultitaskWrapper(task_metrics, prefix=None, postfix=None)` | Combine metrics for named tasks with different input keys. | Inputs must be structured by task. |
| `MetricTracker` | `MetricTracker(metric, maximize=None)` | Keep per-step or per-epoch metric instances and query best/current/all values. | Call `increment()` before update/compute. `maximize` must be inferable or explicit. |
| `Running` | `Running(base_metric, window)` | Track a rolling version of a base metric. | Window size and state reset affect interpretation. |
| `FeatureShare` | `FeatureShare(metrics, max_cache_size=None)` | Share expensive feature computations between compatible metrics. | Requires compatible metrics and can increase cache memory. |
| `MetricInputTransformer` | `MetricInputTransformer(wrapped_metric, **kwargs)` | Adapt input names before passing them to a metric. | Keep transformed keys aligned with metric signatures. |
| `LambdaInputTransformer` | `LambdaInputTransformer(wrapped_metric, transform_pred=None, transform_target=None)` | Apply simple functions to predictions or targets. | Transformations should be deterministic and shape-preserving unless intended. |
| `BinaryTargetTransformer` | `BinaryTargetTransformer(wrapped_metric, threshold=0)` | Convert targets for binary-style metrics. | Check threshold and target semantics. |

## Relationship to core API

All wrappers contain `Metric` objects and therefore inherit the same state, device, reset, and synchronization concerns described in `../core-api/`. If a wrapper behaves strangely, inspect the wrapped metric's state and return type first.
