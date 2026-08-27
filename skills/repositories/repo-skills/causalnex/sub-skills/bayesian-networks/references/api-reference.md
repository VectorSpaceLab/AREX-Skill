# Bayesian Networks API Reference

## Core network

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

Key facts:
- The structure must be a single connected DAG.
- `fit_node_states` learns all observed states from the dataframe.
- `fit_cpds` accepts `MaximumLikelihoodEstimator` or `BayesianEstimator`.
- `fit_latent_cpds` is the latent-variable EM entry point.

## Inference

- `InferenceEngine(bn)`
- `InferenceEngine.query(observations=None, parallel=False, num_cores=None)`
- `InferenceEngine.do_intervention(node, state)`
- `InferenceEngine.reset_do(observation)`

Notes:
- `query()` accepts a dict, a list of dicts, or `None`.
- `do_intervention()` accepts a single state or a full probability map.
- Valid node names must match `^[0-9a-zA-Z_]+$`.

## Evaluation and plotting

- `roc_auc(bn, data, node) -> (roc_points, auc)`
- `classification_report(bn, data, node) -> dict`
- `plot_structure(sm, all_node_attributes=None, all_edge_attributes=None, node_attributes=None, edge_attributes=None, plot_options=None) -> pyvis.network.Network`
- `display_plot_ipython(viz, output_filename, layout_kwargs=None)`

## BayesianNetworkClassifier

- `BayesianNetworkClassifier(list_of_edges, discretiser_alg=None, discretiser_kwargs=None, probability_kwargs=None, return_prob=False)`
- `fit(X, y)`
- `predict(X)`
- `score(X, y, sample_weight=None)`

Notes:
- `discretiser_alg` values: `unsupervised`, `tree`, `mdlp`.
- `discretiser_alg` and `discretiser_kwargs` must share the same keys.
- Set `return_prob=True` to return per-state probabilities instead of hard predictions.

## Latent-variable EM

- `EMSingleLatentVariable(sm, data, lv_name, node_states, initial_params="random", seed=22, box_constraints=None, priors=None, non_missing_data_factor=1, n_jobs=1)`
- `run(n_runs, stopping_delta=0.0, verbose=0)`
- `e_step()`
- `m_step()`
- `apply_box_constraints()`
- `get_default_priors(sm, node_states, lv_name)`
- `get_default_box(sm, node_states, lv_name)`

Notes:
- Use `np.nan` for missing latent-variable values.
- `n_jobs=-1` uses all CPUs.
