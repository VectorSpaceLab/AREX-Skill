# Featuretools API Reference

This file groups the public APIs that the sub-skills rely on. Use it when you need signatures, parameter names, or the rough object relationships without reopening the source repository.

## EntitySet And Demo Data

### Constructors

- `EntitySet(id=None, dataframes=None, relationships=None)`
- `Relationship(entityset, parent_dataframe_name, parent_column_name, child_dataframe_name, child_column_name)`
- `Timedelta(value, unit=None, delta_obj=None)`

### EntitySet Methods

- `EntitySet.add_dataframe(dataframe, dataframe_name=None, index=None, logical_types=None, semantic_tags=None, make_index=False, time_index=None, secondary_time_index=None, already_sorted=False)`
- `EntitySet.normalize_dataframe(base_dataframe_name, new_dataframe_name, index, additional_columns=None, copy_columns=None, make_time_index=None, make_secondary_time_index=None, new_dataframe_time_index=None, new_dataframe_secondary_time_index=None)`
- `EntitySet.add_relationship(parent_dataframe_name=None, parent_column_name=None, child_dataframe_name=None, child_column_name=None, relationship=None)`
- `EntitySet.add_relationships(relationships)`
- `EntitySet.add_last_time_indexes(updated_dataframes=None)`
- `EntitySet.add_interesting_values(max_values=5, verbose=False, dataframe_name=None, values=None)`
- `EntitySet.set_secondary_time_index(dataframe_name, secondary_time_index)`
- `EntitySet.find_forward_paths(start_dataframe_name, goal_dataframe_name)`
- `EntitySet.find_backward_paths(start_dataframe_name, goal_dataframe_name)`
- `EntitySet.get_forward_dataframes(dataframe_name, deep=False)`
- `EntitySet.get_backward_dataframes(dataframe_name, deep=False)`
- `EntitySet.query_by_values(dataframe_name, instance_vals, column_name=None, columns=None, time_last=None, training_window=None, include_cutoff_time=True)`
- `EntitySet.concat(other, inplace=False)`
- `EntitySet.replace_dataframe(dataframe_name, df, already_sorted=False, recalculate_last_time_indexes=True)`
- `EntitySet.to_pickle(path, compression=None, profile_name=None)`
- `EntitySet.to_csv(path, sep=',', encoding='utf-8', engine='python', compression=None, profile_name=None)`
- `EntitySet.to_parquet(path, engine='auto', compression=None, profile_name=None)`
- `EntitySet.plot(to_file=None)`
- `EntitySet.__getitem__(dataframe_name)`

### Demo Loaders

- `load_mock_customer(n_customers=5, n_products=5, n_sessions=35, n_transactions=500, random_seed=0, return_single_table=False, return_entityset=False)`
- `load_retail(id='demo_retail_data', nrows=None, return_single_table=False)`
- `load_flight(month_filter=None, categorical_filter=None, nrows=None, demo=True, return_single_table=False, verbose=False)`
- `load_weather(nrows=None, return_single_table=False)`

### Notes

- `load_mock_customer(return_entityset=True)` is the safest default demo loader.
- `to_parquet` requires `pyarrow`.
- `plot` requires the Python `graphviz` package and the system Graphviz binary.

## DFS And Feature Matrix Generation

### Core Entry Points

- `dfs(dataframes=None, relationships=None, entityset=None, target_dataframe_name=None, cutoff_time=None, instance_ids=None, agg_primitives=None, trans_primitives=None, groupby_trans_primitives=None, allowed_paths=None, max_depth=2, ignore_dataframes=None, ignore_columns=None, primitive_options=None, seed_features=None, drop_contains=None, drop_exact=None, where_primitives=None, max_features=-1, cutoff_time_in_index=False, save_progress=None, features_only=False, training_window=None, approximate=None, chunk_size=None, n_jobs=1, dask_kwargs=None, verbose=False, return_types=None, progress_callback=None, include_cutoff_time=True)`
- `DeepFeatureSynthesis(target_dataframe_name, entityset, agg_primitives=None, trans_primitives=None, where_primitives=None, groupby_trans_primitives=None, max_depth=2, max_features=-1, allowed_paths=None, ignore_dataframes=None, ignore_columns=None, primitive_options=None, seed_features=None, drop_contains=None, drop_exact=None, where_stacking_limit=1)`
- `calculate_feature_matrix(features, entityset=None, cutoff_time=None, instance_ids=None, dataframes=None, relationships=None, cutoff_time_in_index=False, training_window=None, approximate=None, save_progress=None, verbose=False, chunk_size=None, n_jobs=1, dask_kwargs=None, progress_callback=None, include_cutoff_time=True)`
- `encode_features(feature_matrix, features, top_n=10, include_unknown=True, to_encode=None, inplace=False, drop_first=False, verbose=False)`
- `get_valid_primitives(entityset, target_dataframe_name, max_depth=2, selected_primitives=None, **dfs_kwargs)`

### Time And Parallel Helpers

- `make_temporal_cutoffs(instance_ids, cutoffs, window_size=None, num_windows=None, start=None)`
- `bin_cutoff_times(cutoff_time, bin_size)`
- `approximate_features(feature_set, cutoff_time, window, entityset, training_window=None, include_cutoff_time=True)`
- `create_client_and_cluster(n_jobs, dask_kwargs, entityset_size)`
- `replace_inf_values(feature_matrix, replacement_value=nan, columns=None)`
- `convert_time_units(secs, unit)`
- `calculate_trend(series)`
- `convert_datetime_to_floats(x)`
- `convert_timedelta_to_floats(x)`

### Notes

- `n_jobs > 1` is a Dask-backed path and needs the `featuretools[dask]` extras plus `distributed`.
- `include_cutoff_time`, `training_window`, and `cutoff_time_in_index` determine how rows are filtered before feature calculation.
- `encode_features` works on an already-calculated feature matrix; it does not create features by itself.

## Feature Inspection, Recommendation, And Selection

### Discovery Helpers

- `show_info()`
- `list_primitives()`
- `summarize_primitives()`
- `get_recommended_primitives(entityset, include_time_series_primitives=False, excluded_primitives=...)`

### Selection Helpers

- `remove_low_information_features(feature_matrix, features=None)`
- `remove_highly_null_features(feature_matrix, features=None, pct_null_threshold=0.95)`
- `remove_single_value_features(feature_matrix, features=None, count_nan_as_value=False)`
- `remove_highly_correlated_features(feature_matrix, features=None, pct_corr_threshold=0.95, features_to_check=None, features_to_keep=None)`
- `replace_inf_values(feature_matrix, replacement_value=nan, columns=None)`

### Notes

- `get_recommended_primitives` only supports single-table entitysets.
- `show_info` prints package version, install location, system info, and selected dependency versions.
- The selection helpers return a filtered feature matrix and, when a feature list is provided, an aligned feature list.

## Feature Objects, Descriptions, And Serialization

### Constructors

- `Feature(base, dataframe_name=None, groupby=None, parent_dataframe_name=None, primitive=None, use_previous=None, where=None)`
- `FeatureBase(dataframe, base_features, relationship_path, primitive, name=None, names=None)`
- `IdentityFeature(column, name=None)`
- `DirectFeature(base_feature, child_dataframe_name, relationship=None, name=None)`
- `TransformFeature(base_features, primitive, name=None)`
- `AggregationFeature(base_features, parent_dataframe_name, primitive, relationship_path=None, use_previous=None, where=None, name=None)`
- `GroupByTransformFeature(base_features, primitive, groupby, name=None)`
- `FeatureOutputSlice(base_feature, n, name=None)`

### Common Methods

- `FeatureBase.to_dictionary()`
- `FeatureBase.get_name()`
- `FeatureBase.get_feature_names()`
- `FeatureBase.get_dependencies(deep=False, ignored=None, copy=True)`
- `FeatureBase.get_depth(stop_at=None)`
- `FeatureBase.copy()`
- `FeatureBase.__getitem__(key)`
- `FeatureBase.unique_name()`
- `describe_feature(feature, feature_descriptions=None, primitive_templates=None, metadata_file=None)`
- `graph_feature(feature, to_file=None, description=False, **kwargs)`
- `save_features(features, location=None, profile_name=None)`
- `load_features(features, profile_name=None)`

### Primitive Base Classes

- `PrimitiveBase()`
- `TransformPrimitive()`
- `AggregationPrimitive()`

### Primitive Base Methods

- `PrimitiveBase.get_function()`
- `PrimitiveBase.get_args_string()`
- `PrimitiveBase.generate_name()`
- `PrimitiveBase.generate_names()`
- `PrimitiveBase.get_filepath(filename)`
- `TransformPrimitive.generate_name(base_feature_names)`
- `TransformPrimitive.generate_names(base_feature_names)`
- `AggregationPrimitive.generate_name(base_feature_names, relationship_path_name, parent_dataframe_name, where_str, use_prev_str)`
- `AggregationPrimitive.generate_names(base_feature_names, relationship_path_name, parent_dataframe_name, where_str, use_prev_str)`

### Notes

- `FeatureOutputSlice` is how multi-output primitives are split into individually addressable outputs.
- `graph_feature` returns a `graphviz.Digraph` and may also write files when `to_file` is supplied.
- `save_features` and `load_features` accept local paths, file-like objects, and supported remote URLs; S3 support depends on the optional `smart_open`/`boto3` path.
- The top-level import process can load feature-tools plugins from entry points and may log warnings when an extension fails to load.
