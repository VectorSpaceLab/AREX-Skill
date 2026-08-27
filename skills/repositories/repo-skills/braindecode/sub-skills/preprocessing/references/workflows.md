# Preprocessing workflows

Create a local MNE `RawArray` or small braindecode dataset, inspect `info`, then
apply one operation at a time. Confirm units explicitly: MNE data are commonly
volts, while many deep-learning recipes convert to microvolts before fitting.
Keep that conversion identical at inference.

Use raw/continuous preprocessing before event or fixed windowing when filters,
resampling, or artifact operations need context. Create windows, then apply
channel-wise normalization when the operation is intended per window. Recompute
`window_size_samples` and stride after resampling.

Start with `n_jobs=1` and `preload=True` for debugging. Once results are stable,
use `save_dir` for serialization and increase `n_jobs`; parallel processing can
increase memory use and may require picklable callables. Use `overwrite=True`
only when the cache key and parameters have been checked.

EEGPrep is an optional extra. Treat it as an explicit preprocessing stage and
verify its version/API separately; do not make a baseline pipeline depend on
it.
