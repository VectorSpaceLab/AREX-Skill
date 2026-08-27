# API Reference

This page collects the public CausalNex entry points that matter most for day-to-day use. It is organized by workflow so you can jump to the right section without reopening the source tree.

## 1. Structure learning

### Graph container
- `causalnex.structure.StructureModel(incoming_graph_data=None, origin="unknown", **attr)`
- `StructureModel.add_edge(u, v, origin="unknown", **attr)`
- `StructureModel.add_edges_from(ebunch_to_add, origin="unknown", **attr)`
- `StructureModel.add_weighted_edges_from(ebunch_to_add, weight="weight", origin="unknown", **attr)`
- `StructureModel.remove_edges_below_threshold(threshold)`
- `StructureModel.get_markov_blanket(nodes)`

Notes:
- Edges carry an `origin` attribute: `unknown`, `learned`, or `expert`.
- Cycles are allowed in `StructureModel` but not in `BayesianNetwork`.

### NOTEARS and wrappers
- `causalnex.structure.notears.from_pandas(X, max_iter=100, h_tol=1e-8, w_threshold=0.0, tabu_edges=None, tabu_parent_nodes=None, tabu_child_nodes=None) -> StructureModel`
- `causalnex.structure.notears.from_numpy(X, max_iter=100, h_tol=1e-8, w_threshold=0.0, tabu_edges=None, tabu_parent_nodes=None, tabu_child_nodes=None) -> StructureModel`
- `causalnex.structure.pytorch.notears.from_pandas(X, dist_type_schema=None, lasso_beta=0.0, ridge_beta=0.0, use_bias=False, hidden_layer_units=None, max_iter=100, w_threshold=None, tabu_edges=None, tabu_parent_nodes=None, tabu_child_nodes=None, use_gpu=True, **kwargs) -> StructureModel`
- `causalnex.structure.pytorch.notears.from_numpy(X, dist_type_schema=None, lasso_beta=0.0, ridge_beta=0.0, use_bias=False, hidden_layer_units=None, w_threshold=None, max_iter=100, tabu_edges=None, tabu_parent_nodes=None, tabu_child_nodes=None, use_gpu=True, **kwargs) -> StructureModel`

Notes:
- The legacy `causalnex.structure.notears` path does not accept `use_gpu`, `dist_type_schema`, lasso/ridge parameters, or hidden layers.
- Use `causalnex.structure.pytorch.notears` for distribution schemas, nonlinear hidden layers, and CPU/GPU control.
- `use_gpu=True` only uses CUDA when torch can see a CUDA device.
- Both structure-learning paths expect numeric data and reject NaN or infinity.
- `dist_type_schema` aliases in the PyTorch path: `bin`, `cat`, `cont`, `ord`, `poiss`.

### Dynamic structure learning
- `causalnex.structure.dynotears.from_pandas_dynamic(time_series, p, lambda_w=0.1, lambda_a=0.1, max_iter=100, h_tol=1e-8, w_threshold=0.0, tabu_edges=None, tabu_parent_nodes=None, tabu_child_nodes=None) -> StructureModel`
- `causalnex.structure.dynotears.from_numpy_dynamic(X, Xlags, lambda_w=0.1, lambda_a=0.1, max_iter=100, h_tol=1e-8, w_threshold=0.0, tabu_edges=None, tabu_parent_nodes=None, tabu_child_nodes=None) -> StructureModel`

### Sklearn wrappers
- `causalnex.structure.pytorch.sklearn.DAGClassifier(dist_type_schema=None, alpha=0.0, beta=0.0, fit_intercept=True, hidden_layer_units=None, threshold=0.0, tabu_edges=None, tabu_parent_nodes=None, tabu_child_nodes=None, dependent_target=True, enforce_dag=False, standardize=False, target_dist_type=None, notears_mlp_kwargs=None)`
- `causalnex.structure.pytorch.sklearn.DAGRegressor(dist_type_schema=None, alpha=0.0, beta=0.0, fit_intercept=True, hidden_layer_units=None, threshold=0.0, tabu_edges=None, tabu_parent_nodes=None, tabu_child_nodes=None, dependent_target=True, enforce_dag=False, standardize=False, target_dist_type=None, notears_mlp_kwargs=None)`
- Shared base methods:
  - `DAGBase.fit(X, y)`
  - `DAGBase.predict(X)`
  - `DAGBase.plot_dag(output_filename, enforce_dag=False, plot_structure_kwargs=None, layout_kwargs=None)`

Notes:
- `DAGClassifier` exposes `predict`, `predict_proba`, `feature_importances_`, and `classes_`.
- `DAGRegressor` is the regression counterpart with the same NOTEARS backbone.

## 2. Bayesian networks and inference

### BayesianNetwork
- `BayesianNetwork(structure)`
- `BayesianNetwork.node_states`
- `BayesianNetwork.cpds`
- `BayesianNetwork.set_cpd(node, df)`
- `BayesianNetwork.fit_node_states(df)`
- `BayesianNetwork.fit_cpds(data, method="MaximumLikelihoodEstimator", bayes_prior=None, equivalent_sample_size=None)`
- `BayesianNetwork.fit_node_states_and_cpds(data, method="MaximumLikelihoodEstimator", bayes_prior=None, equivalent_sample_size=None)`
- `BayesianNetwork.fit_latent_cpds(lv_name, lv_states, data, box_constraints=None, priors=None, initial_params="random", non_missing_data_factor=1, n_runs=20, stopping_delta=0.0)`
- `BayesianNetwork.predict(data, node)`
- `BayesianNetwork.predict_probability(data, node)`
- `BayesianNetwork.add_node(node, edges_to_add, edges_to_remove)`

### InferenceEngine
- `InferenceEngine(bn)`
- `InferenceEngine.query(observations=None, parallel=False, num_cores=None)`
- `InferenceEngine.do_intervention(node, state)`
- `InferenceEngine.reset_do(observation)`

Notes:
- `InferenceEngine` requires valid node names and fitted CPDs.
- `do_intervention` accepts a single state or a full state-probability map.

### Evaluation and plotting
- `roc_auc(bn, data, node) -> (roc_points, auc)`
- `classification_report(bn, data, node) -> dict`
- `plot_structure(sm, all_node_attributes=None, all_edge_attributes=None, node_attributes=None, edge_attributes=None, plot_options=None) -> pyvis.network.Network`
- `display_plot_ipython(viz, output_filename, layout_kwargs=None)`

### BayesianNetworkClassifier
- `BayesianNetworkClassifier(list_of_edges, discretiser_alg=None, discretiser_kwargs=None, probability_kwargs=None, return_prob=False)`
- `fit(X, y)`
- `predict(X)`
- `score(X, y, sample_weight=None)`

Notes:
- `discretiser_alg` accepts `unsupervised`, `tree`, or `mdlp` per feature.
- `discretiser_alg` and `discretiser_kwargs` must have the same keys.

### Latent-variable EM
- `EMSingleLatentVariable(sm, data, lv_name, node_states, initial_params="random", seed=22, box_constraints=None, priors=None, non_missing_data_factor=1, n_jobs=1)`
- `run(n_runs, stopping_delta=0.0, verbose=0)`
- `e_step()`
- `m_step()`
- `apply_box_constraints()`
- `get_default_priors(sm, node_states, lv_name)`
- `get_default_box(sm, node_states, lv_name)`

## 3. Discretization

### Unsupervised discretizer
- `Discretiser(method="uniform", num_buckets=None, outlier_percentile=None, numeric_split_points=None, percentile_split_points=None)`
- `fit(data)`
- `transform(data)`
- `fit_transform(data)`

### Supervised discretizers
- `DecisionTreeSupervisedDiscretiserMethod(mode="single", split_unselected_feat=False, tree_params=None)`
- `MDLPSupervisedDiscretiserMethod(mdlp_args=None)`

Notes:
- `MDLPSupervisedDiscretiserMethod` requires the optional `mdlp-discretization` package.
- `DecisionTreeSupervisedDiscretiserMethod` stores thresholds in `map_thresholds`.
- `extract_thresholds_from_dtree(dtree, length_df)` is a helper used by the tree-based path.

## 4. Synthetic data and utilities

### Data generators
- `generate_structure(num_nodes, degree, graph_type="erdos-renyi", w_min=0.5, w_max=0.5)`
- `sem_generator(graph, schema=None, default_type="continuous", noise_std=1.0, n_samples=1000, distributions=None, intercept=True, seed=None)`
- `nonlinear_sem_generator(graph, kernel, default_type=..., ...)`
- `generate_continuous_data(sm, n_samples, distribution="gaussian", noise_scale=1.0, intercept=False, seed=None, kernel=None)`
- `generate_binary_data(sm, n_samples, distribution="logit", noise_scale=1.0, intercept=False, seed=None, kernel=None)`
- `generate_count_dataframe(sm, n_samples, zero_inflation_factor=0.1, intercept=False, seed=None, kernel=None)`
- `generate_categorical_dataframe(sm, n_samples, distribution="logit", n_categories=3, noise_scale=1.0, intercept=False, seed=None, kernel=None)`
- `generate_structure_dynamic(num_nodes, p, degree_intra, degree_inter, graph_type_intra="erdos-renyi", graph_type_inter="erdos-renyi", w_min_intra=0.5, w_max_intra=0.5, w_min_inter=0.5, w_max_inter=0.5, w_decay=1.0)`
- `generate_dataframe_dynamic(g, n_samples=1000, burn_in=100, sem_type="linear-gauss", noise_scale=1.0, drift=None)`
- `gen_stationary_dyn_net_and_df(num_nodes=10, n_samples=100, p=1, degree_intra=3, degree_inter=3, graph_type_intra="erdos-renyi", graph_type_inter="erdos-renyi", w_min_intra=0.5, w_max_intra=0.5, w_min_inter=0.5, w_max_inter=0.5, w_decay=1.0, sem_type="linear-gauss", noise_scale=1, max_data_gen_trials=1000)`

### Transform and mapping helpers
- `DynamicDataTransformer(p)`
- `DynamicDataTransformer.fit(time_series, return_df=True)`
- `DynamicDataTransformer.transform(time_series)`
- `VariableFeatureMapper(schema)`
- `validate_schema(nodes, default_type="continuous", schema=None)`
- `states_to_df(node_states)`
- `count_unique_rows(data, placeholder=-inf)`
- `chunk_data(df, n_chunks)`

Notes:
- Dynamic transformer output uses `{feature}_lag0`, `{feature}_lag1`, etc.
- `VariableFeatureMapper` expects types such as `binary`, `categorical:3`, `continuous`, and `count`.
- `states_to_df` pads state lists to the maximum state cardinality across nodes.
- `chunk_data` yields dataframe chunks; wrap it with `list(...)` when you need to count or index the chunks.
