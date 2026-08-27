# Evaluation and Benchmarking API Reference

Verified signatures:

- `temporal_train_test_split(y, X=None, test_size=None, train_size=None, fh=None, anchor='start')`.
- `SlidingWindowSplitter(fh=1, window_length=10, step_length=1, initial_window=None, start_with_window=True)`.
- `ExpandingWindowSplitter(fh=1, initial_window=10, step_length=1)`.
- `mean_absolute_percentage_error(y_true, y_pred, horizon_weight=None, multioutput='uniform_average', symmetric=False, relative_to='y_true', **kwargs)`.
- `evaluate(forecaster, cv, y, X=None, strategy='refit', scoring=None, return_data=False, error_score=nan, backend=None, ...)`.
- `ForecastingBenchmark(id_format=None, backend=None, backend_params=None, return_data=False)`.

Metrics exist as both functions and callable classes. Callable classes expose names used in evaluation result columns, e.g. `test_MeanAbsolutePercentageError`.

## Splitter selection

Use `temporal_train_test_split` for one final holdout. Use sliding or expanding windows for repeated backtests. Use instance splitters only when splitting complete panel instances rather than future time points.

## Benchmarking classes

Benchmark classes collect estimators, tasks, splitters, scorers, storage, and analysis. Keep benchmark IDs stable and make storage paths user-controlled when writing artifacts.
