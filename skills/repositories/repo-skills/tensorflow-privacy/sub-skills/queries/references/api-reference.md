# Queries API reference

## Purpose

Read this for the verified query constructors and the low-level helper modules that support them.

## Core abstract surface

### `DPQuery`

The base query type exported from `tensorflow_privacy.privacy.dp_query.dp_query`.

### `SumAggregationDPQuery`

The main base class for sum-aggregation query families.

## Verified constructor signatures

- `GaussianSumQuery(l2_norm_clip, stddev)`
- `DiscreteGaussianSumQuery(l2_norm_bound, stddev)`
- `DistributedDiscreteGaussianSumQuery(l2_norm_bound, local_stddev)`
- `DistributedSkellamSumQuery(l1_norm_bound, l2_norm_bound, local_stddev)`
- `DistributedSkellamAverageQuery(l1_norm_bound, l2_norm_bound, local_stddev, denominator)`
- `NestedQuery(queries)`
- `NestedSumQuery(queries)`
- `NoPrivacySumQuery()`
- `NoPrivacyAverageQuery()`
- `NormalizedQuery(numerator_query, denominator)`
- `QuantileEstimatorQuery(initial_estimate, target_quantile, learning_rate, below_estimate_stddev, expected_num_records, geometric_update=False)`
- `NoPrivacyQuantileEstimatorQuery(initial_estimate, target_quantile, learning_rate, geometric_update=False)`
- `TreeQuantileEstimatorQuery(initial_estimate, target_quantile, learning_rate, below_estimate_stddev, expected_num_records, geometric_update=False)`
- `QuantileAdaptiveClipSumQuery(initial_l2_norm_clip, noise_multiplier, target_unclipped_quantile, learning_rate, clipped_count_stddev, expected_num_records, geometric_update=True)`
- `QAdaClipTreeResSumQuery(initial_l2_norm_clip, noise_multiplier, record_specs, target_unclipped_quantile, learning_rate, clipped_count_stddev, expected_num_records, geometric_update=True, noise_seed=None)`
- `RestartQuery(inner_query, restart_indicator)`
- `PeriodicRoundRestartIndicator(period, warmup=None)`
- `PeriodicTimeRestartIndicator(period_seconds)`
- `TreeCumulativeSumQuery(record_specs, noise_generator, clip_fn, clip_value, use_efficient=True)`
- `TreeResidualSumQuery(record_specs, noise_generator, clip_fn, clip_value, use_efficient=True)`
- `TreeRangeSumQuery(inner_query, arity=2)`

## Helper modules

### `dp_query.test_utils`

`run_query(query, records, global_state=None, weights=None)` is the simplest smoke harness for a query. It initializes global state if needed, feeds the records through the query, and returns `(result, new_global_state)`.

### `tree_aggregation`

Public helper classes and functions include:

- `ValueGenerator`
- `GaussianNoiseGenerator(noise_std, specs, seed=None)`
- `StatelessValueGenerator(value_fn)`
- `TreeState`
- `get_step_idx(state)`
- `TreeAggregator(value_generator)`

Use these when the user is working below the query wrapper layer.

## Decision points

- Use `NoPrivacy*` only when the user explicitly wants a non-private baseline or a debugging comparison.
- Use `NormalizedQuery` when a numerator query must be scaled by a separate denominator.
- Use nested or tree-aggregation queries only when the user's mechanism is truly composite; otherwise keep the query simple.
