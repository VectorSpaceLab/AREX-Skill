# Backends and outputs

PyMC 6.3.0 returns xarray `DataTree` outputs by default. Common groups: `posterior`, `sample_stats`, `prior`, `prior_predictive`, `observed_data`, `constant_data`, `posterior_predictive`, `predictions`, and `log_likelihood`.

Use `pm.compute_log_likelihood(idata, model=model)` when `log_likelihood` is needed for model comparison and was not created during sampling.

Legacy `return_inferencedata=False` returns `MultiTrace` and is deprecated for many workflows. External NUTS routes do not support it.

Zarr and `mcbackend` are optional trace/storage integrations. Use them only when persistent/chunked storage or a specific backend integration is required; ordinary tasks should use default DataTree outputs.
