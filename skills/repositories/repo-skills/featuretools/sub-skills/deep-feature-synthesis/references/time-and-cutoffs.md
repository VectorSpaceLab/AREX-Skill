# Time And Cutoffs

## Main Helpers

- `Timedelta(value, unit=None, delta_obj=None)`
- `make_temporal_cutoffs(instance_ids, cutoffs, window_size=None, num_windows=None, start=None)`
- `bin_cutoff_times(cutoff_time, bin_size)`
- `approximate_features(feature_set, cutoff_time, window, entityset, training_window=None, include_cutoff_time=True)`
- `calculate_trend(series)`
- `convert_time_units(secs, unit)`

## How To Think About Them

### `Timedelta`

Use `Timedelta` when a feature-generation workflow needs a relative time window such as "2 days" or "4 weeks" rather than a raw integer.

### `make_temporal_cutoffs`

Use this helper when you have instance ids and one or more cutoff points and want a compact cutoff table instead of building one manually.

It is useful for rolling-window or time-series examples because it keeps the row order and cutoff logic explicit.

### `bin_cutoff_times`

Use this when a series of cutoff times should be grouped into regular bins before feature calculation.

### `approximate_features`

Use this when the feature-matrix workflow should compute approximate windows for expensive aggregation features.

It is part of the performance path and is not required for ordinary tiny-smoke DFS.

### `calculate_trend`

This helper is used by time-series primitives that need a trend over a numeric series.

## Example Pattern

1. Build or load a valid EntitySet.
2. Create a small cutoff table.
3. Decide whether the time window should be exact or approximate.
4. Re-run DFS or `calculate_feature_matrix` with the time settings.
5. Compare the resulting matrix shape or a few key feature values.

## Common Pitfalls

- A cutoff table with the wrong instance id column or time type will usually fail before the feature calculation starts.
- A time window that is too restrictive can eliminate every row.
- `include_cutoff_time=False` can change the row count even when the feature definitions are identical.
