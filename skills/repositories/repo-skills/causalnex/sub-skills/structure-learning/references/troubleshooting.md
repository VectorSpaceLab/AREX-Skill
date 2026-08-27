# Structure Learning Troubleshooting

## Data validation

- `All columns must have numeric data`: encode categoricals before calling `from_pandas` or `from_numpy`.
- `Input contains NaN, infinity or a value too large for ...`: clean or impute the data first.
- `Difference indices and expected indices`: ensure `dist_type_schema` covers every column or positional index.

## Convergence and constraints

- `Failed to converge. Consider increasing max_iter.`: raise `max_iter`, shrink the model, or add more tabu constraints.
- Very dense graphs: increase `w_threshold` or `lasso_beta`.
- Empty output: make sure the data actually contains signal and the threshold is not too aggressive.

## Dynamic data issues

- `Input data X and Xlags must have the same number of rows`: the lagged matrix must align with the current observations.
- `Number of columns of Xlags must be a multiple of number of columns of X`: use the same feature count when preparing lagged arrays.
- Lag naming surprises: dynamic outputs always use `{feature}_lag0`, `{feature}_lag1`, and so on.

## Wrapper issues

- `DAGClassifier` or `DAGRegressor` fit errors often mean the target shape is wrong or the data is not numeric.
- `plot_dag` problems usually come from missing HTML output support or a broken `pyvis` install.
- If GPU-related calls fail, retry with `use_gpu=False` and repair the torch installation only after the CPU path works.
