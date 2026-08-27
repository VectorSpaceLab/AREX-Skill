# Synthetic Data API Reference

## DAG and data generators

- `generate_structure(num_nodes, degree, graph_type="erdos-renyi", w_min=0.5, w_max=0.5) -> StructureModel`
- `sem_generator(graph, schema=None, default_type="continuous", noise_std=1.0, n_samples=1000, distributions=None, intercept=True, seed=None) -> pd.DataFrame`
- `nonlinear_sem_generator(graph, kernel, default_type=..., ...)`
- `generate_continuous_data(sm, n_samples, distribution="gaussian", noise_scale=1.0, intercept=False, seed=None, kernel=None) -> np.ndarray`
- `generate_binary_data(sm, n_samples, distribution="logit", noise_scale=1.0, intercept=False, seed=None, kernel=None) -> np.ndarray`
- `generate_count_dataframe(sm, n_samples, zero_inflation_factor=0.1, intercept=False, seed=None, kernel=None) -> pd.DataFrame`
- `generate_categorical_dataframe(sm, n_samples, distribution="logit", n_categories=3, noise_scale=1.0, intercept=False, seed=None, kernel=None) -> pd.DataFrame`

## Dynamic DAG and time-series helpers

- `generate_structure_dynamic(num_nodes, p, degree_intra, degree_inter, graph_type_intra="erdos-renyi", graph_type_inter="erdos-renyi", w_min_intra=0.5, w_max_intra=0.5, w_min_inter=0.5, w_max_inter=0.5, w_decay=1.0) -> StructureModel`
- `generate_dataframe_dynamic(g, n_samples=1000, burn_in=100, sem_type="linear-gauss", noise_scale=1.0, drift=None) -> pd.DataFrame`
- `gen_stationary_dyn_net_and_df(num_nodes=10, n_samples=100, p=1, degree_intra=3, degree_inter=3, graph_type_intra="erdos-renyi", graph_type_inter="erdos-renyi", w_min_intra=0.5, w_max_intra=0.5, w_min_inter=0.5, w_max_inter=0.5, w_decay=1.0, sem_type="linear-gauss", noise_scale=1, max_data_gen_trials=1000)`

## Transform and mapping helpers

- `DynamicDataTransformer(p)`
- `DynamicDataTransformer.fit(time_series, return_df=True)`
- `DynamicDataTransformer.transform(time_series)`
- `VariableFeatureMapper(schema)`
- `validate_schema(nodes, default_type="continuous", schema=None)`
- `states_to_df(node_states)`
- `count_unique_rows(data, placeholder=-inf)`
- `chunk_data(df, n_chunks)`

## Practical notes

- Dynamic transforms emit `*_lag0`, `*_lag1`, etc.
- Categorical schemas use values like `categorical:3`.
- `states_to_df` pads state lists to the maximum state cardinality across nodes.
- `chunk_data` yields dataframe chunks; wrap it in `list(...)` before counting or indexing chunks.
- Synthetic generators are useful for tiny smoke tests and fixture creation before you move to real data.
