# Tabular API reference

This reference narrows the root Libra API surface to the structured-data workflows most users ask about.

## Core client methods

| Method | Use it when | Important inputs | Stored key / result |
|---|---|---|---|
| `neural_network_query(instruction, ...)` | You want Libra to choose regression vs classification from the target column. | `instruction`, `epochs`, `text`, `drop`, `preprocess`, `ca_threshold`, `test_size`, `save_model` | `regression_ANN` or `classification_ANN` depending on target cardinality. |
| `regression_query_ann(instruction, ...)` | The target is numeric and you want the feed-forward regression path directly. | `instruction`, `text`, `drop`, `test_size`, `epochs`, `save_model=False` for smoke runs, `save_path` | `regression_ANN` with `model`, `preprocessor`, `interpreter`, `losses`, and `test_data`. |
| `classification_query_ann(instruction, ...)` | The target is categorical and you want the feed-forward classification path directly. | `instruction`, `text`, `drop`, `test_size`, `epochs`, `save_path` | `classification_ANN` with `model`, `preprocessor`, `interpreter`, `losses`, `accuracy`, and `test_data`. |
| `svm_query(instruction, ...)` | You want a linear or kernel SVM classifier. | `kernel`, `test_size`, `text`, `drop`, `cross_val_size`, `degree`, `gamma`, `coef0`, `max_iter` | `svm` with `accuracy`, `losses`, `plots`, `preprocessor`, and `interpreter`. |
| `nearest_neighbor_query(instruction, ...)` | You want a KNN classifier and a sweep over neighbor counts. | `min_neighbors`, `max_neighbors`, `leaf_size`, `p`, `algorithm` | `nearest_neighbor` with similar stored fields to other classifiers. |
| `decision_tree_query(instruction, ...)` | You want a decision-tree classifier. | `criterion`, `splitter`, `max_depth`, `min_samples_*`, `ccp_alpha` | `decision_tree`. |
| `xgboost_query(instruction, ...)` | You want XGBoost classification. | `learning_rate`, `n_estimators`, `max_depth`, `subsample`, `colsample_bytree`, `objective` | `xgboost`. |
| `kmeans_clustering_query(...)` | The data is unlabeled or you want unsupervised clusters. | `clusters`, `base_clusters`, `preprocess`, `drop`, `text` | `k_means_clustering` with `model`, `plots`, and clustering metadata. |
| `content_recommender_query(feature_names, indexer, ...)` | You want content-based recommendations from a catalog table. | `feature_names`, `indexer`, `n_recommendations` | `content_recommender`; use `recommend(search_term)` afterward. |
| `tune(model_to_tune, ...)` | You already built a supported ANN/CNN model and want Keras Tuner. | `model_to_tune`, `max_trials`, `max_layers`, `min_layers`, `objective`, `directory` | Replaces the selected model dict with tuned weights and hyperparameters. |
| `predict(data, model=None)` | You want predictions from a stored tabular model. | `data`, optional `model` | Uses the selected/latest model and its stored preprocessor/interpreter. |
| `analyze(model=None, save=True, save_model=False)` | You want metrics and plots added to a stored model dict. | `model`, `save`, `save_model` | Updates the existing model dict in place. |
| `plots(model=None, plot=None, save=False)` | You want to display or save stored plots. | `model`, `plot`, `save` | Pulls plot objects from the model dict. |
| `info(model=None)` | You want the keys present in a model dict. | `model` | Returns the model-data key listing. |
| `model(model=None)` | You want the full stored dict. | `model` | Returns the selected/latest model dict. |
| `accuracy(model=None)` / `losses(model=None)` / `target(model=None)` / `operators(model=None)` | You want a focused inspection value. | `model` | Returns the stored metric, target, or operator data. |
| `dashboard()` | You want the Streamlit EDA dashboard. | none | Launches the dashboard process. |

## Routing heuristics
- Use the exact method when the task already names the algorithm.
- Use `neural_network_query` when the user only knows they want an ANN and does not care whether it is regression or classification.
- Use `predict`, `info`, `model`, `accuracy`, `losses`, `target`, or `plots` only after a model has already been stored in `client.models`.
- Use `recommend()` only after `content_recommender_query()` has populated `content_recommender`.

## Result dictionaries
Tabular model dictionaries usually contain some combination of:
`id`, `model`, `target`, `plots`, `preprocessor`, `interpreter`, `losses`, `accuracy`, `test_data`, `num_classes`, `data_sizes`, `hyperparameters`, `n_centers`, `centroids`, `inertia`, or `recommendations`.

When writing downstream code, inspect `c.models[model_key].keys()` before assuming that a field exists.
