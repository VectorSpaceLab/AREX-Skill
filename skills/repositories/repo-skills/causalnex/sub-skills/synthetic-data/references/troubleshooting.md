# Synthetic Data Troubleshooting

## Graph generator issues

- `DAG must have at least 2 nodes`: increase `num_nodes` before calling `generate_structure`.
- `Unknown graph type ...`: choose `erdos-renyi`, `barabasi-albert`, or `full` for static graphs.
- `Unknown inter-slice graph type ...`: use `erdos-renyi` or `full` for the dynamic inter-slice generator.
- `Absolute minimum weight must be less than or equal to maximum weight`: swap or widen the weight bounds.

## Data generation issues

- If a generator returns NaNs or overflows, reduce the graph size, lower the degree, or reduce `noise_scale`.
- If `gen_stationary_dyn_net_and_df` cannot find a stable sample, lower the degree or increase `max_data_gen_trials`.
- If a dynamic sample looks too short, remember that `burn_in` rows are discarded before the returned dataframe is built.

## Dynamic transformer issues

- `Provided empty list of time_series`: pass at least one dataframe.
- `All columns must have numeric data`: encode non-numeric columns before calling `DynamicDataTransformer`.
- `Time series entries must be instances of pd.DataFrame`: convert arrays to dataframes first.
- `Index for dataframe must be provided in increasing order`: sort the index before fitting.
- `All inputs must have the same columns and same types`: keep every series aligned before fitting.
- `We should provide all necessary columns`: do not drop required lag columns before transform.

## Feature mapping issues

- `Unsupported variable type`: use one of `binary`, `categorical`, `continuous`, or `count`.
- `categorical` variables must include a cardinality such as `categorical:3`.
- `validate_schema` is the quickest way to check that your intended schema matches the nodes.

## Debug sequence

1. Generate the smallest possible DAG and dataframe.
2. Confirm the dataframe columns and dtypes.
3. Try the dynamic transformer on a tiny two-column example.
4. Only then plug the synthetic output into structure learning or Bayesian-network fitting.
