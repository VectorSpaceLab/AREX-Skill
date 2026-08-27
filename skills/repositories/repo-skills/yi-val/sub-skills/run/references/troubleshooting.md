# Runtime troubleshooting

## Runs block or never return

- CLI `yival run` displays Dash by default. Use the Python API with `display=False` for headless runs.
- Dash threads are joined at the end of `ExperimentRunner.run()`. Close the server/UI when done.
- Provider-backed custom functions can block on rate limits or network calls. Run with one row and one variation first.

## No results or empty experiment

- `DataProcessor` returns an empty iterator if `dataset.reader` or `dataset.file_path` is missing for `source_type: dataset`.
- A config with no `custom_function` returns no custom outputs and skips UI display.
- If all CSV rows have missing values, `CSVReader` skips them and logs warnings.

## Custom function import fails

- Use `package.module.function` when the package is importable.
- For a local file, add its parent directory to `PYTHONPATH` or run from the parent directory.
- Verify the function signature with `inspect.signature()`; every dataset field must match a parameter.

## Variation behavior is wrong

- `StringWrapper` uses its `name` to retrieve the active variation. YAML `variations[].name` must match exactly.
- Pass the active `state` into the wrapper. Without it, wrapper behavior may fall back to a fresh inactive state.
- `ExperimentState` produces the Cartesian product of all variation lists. Too many variations can multiply API calls quickly.

## Evaluator output missing

- `Evaluator` only runs configs whose `evaluator_type` is `individual` during per-result evaluation.
- Comparison evaluators run during group evaluation; all-results evaluators run after experiment aggregation.
- Registry ids must be imported and available before runner dispatch.

## Output pickle path confusion

- `output_path="results.pkl"` writes `results_0.pkl`.
- `experiment_input_path="results.pkl"` reads `results_0.pkl`.
- For YAML lists, increment the index for each config.

## Async pitfalls

- `async_eval=True` is intended for async custom functions. If the function is synchronous but slow, it still runs within the async wrapper path and may not provide the expected concurrency.
- Rate limit handling sleeps for a long interval after broad exceptions in async evaluation. Keep provider tests tiny and explicit.
