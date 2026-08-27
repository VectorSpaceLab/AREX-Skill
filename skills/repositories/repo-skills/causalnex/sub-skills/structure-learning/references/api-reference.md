# Structure Learning API Reference

## Core graph container

- `StructureModel(incoming_graph_data=None, origin="unknown", **attr)`
- `StructureModel.add_edge(u, v, origin="unknown", **attr)`
- `StructureModel.add_edges_from(ebunch_to_add, origin="unknown", **attr)`
- `StructureModel.add_weighted_edges_from(ebunch_to_add, weight="weight", origin="unknown", **attr)`
- `StructureModel.remove_edges_below_threshold(threshold)`

Edges can be marked `unknown`, `learned`, or `expert`. This is useful when you want to mix human edits with learned edges.

## Static NOTEARS

Legacy optimizer:

- `causalnex.structure.notears.from_pandas(X, max_iter=100, h_tol=1e-8, w_threshold=0.0, tabu_edges=None, tabu_parent_nodes=None, tabu_child_nodes=None)`
- `causalnex.structure.notears.from_numpy(X, max_iter=100, h_tol=1e-8, w_threshold=0.0, tabu_edges=None, tabu_parent_nodes=None, tabu_child_nodes=None)`

PyTorch optimizer:

- `causalnex.structure.pytorch.notears.from_pandas(X, dist_type_schema=None, lasso_beta=0.0, ridge_beta=0.0, use_bias=False, hidden_layer_units=None, max_iter=100, w_threshold=None, tabu_edges=None, tabu_parent_nodes=None, tabu_child_nodes=None, use_gpu=True, **kwargs)`
- `causalnex.structure.pytorch.notears.from_numpy(X, dist_type_schema=None, lasso_beta=0.0, ridge_beta=0.0, use_bias=False, hidden_layer_units=None, w_threshold=None, max_iter=100, tabu_edges=None, tabu_parent_nodes=None, tabu_child_nodes=None, use_gpu=True, **kwargs)`

Key facts:
- The legacy `causalnex.structure.notears` functions do not accept `use_gpu`, `dist_type_schema`, lasso/ridge parameters, or hidden layers.
- Use the PyTorch optimizer for distribution schemas, nonlinear hidden layers, and CPU/GPU control.
- `hidden_layer_units=None` means a linear PyTorch NOTEARS model.
- `w_threshold` removes small-weight edges after fitting.
- `tabu_edges`, `tabu_parent_nodes`, and `tabu_child_nodes` are the main constraints.
- `dist_type_schema` uses aliases such as `bin`, `cat`, `cont`, `ord`, `poiss`.

## Dynamic NOTEARS

- `from_pandas_dynamic(time_series, p, lambda_w=0.1, lambda_a=0.1, max_iter=100, h_tol=1e-8, w_threshold=0.0, tabu_edges=None, tabu_parent_nodes=None, tabu_child_nodes=None)`
- `from_numpy_dynamic(X, Xlags, lambda_w=0.1, lambda_a=0.1, max_iter=100, h_tol=1e-8, w_threshold=0.0, tabu_edges=None, tabu_parent_nodes=None, tabu_child_nodes=None)`

Dynamic outputs use nodes like `feature_lag0`, `feature_lag1`, and so on.

## Sklearn wrappers

- `DAGClassifier(dist_type_schema=None, alpha=0.0, beta=0.0, fit_intercept=True, hidden_layer_units=None, threshold=0.0, tabu_edges=None, tabu_parent_nodes=None, tabu_child_nodes=None, dependent_target=True, enforce_dag=False, standardize=False, target_dist_type=None, notears_mlp_kwargs=None)`
- `DAGRegressor(dist_type_schema=None, alpha=0.0, beta=0.0, fit_intercept=True, hidden_layer_units=None, threshold=0.0, tabu_edges=None, tabu_parent_nodes=None, tabu_child_nodes=None, dependent_target=True, enforce_dag=False, standardize=False, target_dist_type=None, notears_mlp_kwargs=None)`
- `DAGBase.fit(X, y)`
- `DAGBase.predict(X)`
- `DAGBase.plot_dag(output_filename, enforce_dag=False, plot_structure_kwargs=None, layout_kwargs=None)`

The classifier handles binary and multiclass targets; the regressor handles continuous targets. Both accept NumPy or pandas inputs. `use_gpu` and `max_iter` are not top-level constructor arguments; pass supported lower-level PyTorch NOTEARS controls through `notears_mlp_kwargs` when needed.

## PyTorch NOTEARS model

- `NotearsMLP(n_features, dist_types, use_bias=False, use_gpu=True, hidden_layer_units=(0,), bounds=None, lasso_beta=0.0, ridge_beta=0.0, nonlinear_clamp=1e-2)`

This is the lower-level model used by the NOTEARS wrappers. Use it only when you need to inspect the optimization or device behavior directly.
