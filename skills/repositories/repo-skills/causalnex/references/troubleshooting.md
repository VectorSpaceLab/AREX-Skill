# Troubleshooting

## Install and import failures

- `ModuleNotFoundError: No module named 'causalnex'`: install the public package in the active Python environment with `pip install causalnex`.
- `ModuleNotFoundError: No module named 'pkg_resources'` while importing `causalnex.network` or `causalnex.inference`: use a setuptools release that still ships `pkg_resources` or pin `setuptools<81` in the active environment.
- Import failures in the PyTorch NOTEARS path usually mean torch is missing or broken. Reinstall a CPU or CUDA build of torch that matches the environment.
- `MDLPSupervisedDiscretiserMethod` import errors mean the optional `mdlp-discretization` package is missing or failed to build.

## Optional dependency failures

- Plotting uses `pyvis`. If plotting imports fail, confirm the package is installed and that the environment can create HTML output.
- Parallel inference uses `pathos`. If `InferenceEngine.query(parallel=True)` fails, keep `parallel=False` or repair the `pathos` install.
- MDLP discretization can need a working C/C++ build toolchain. If build isolation fails, install `Cython` and retry the optional package install.

## Structure-learning failures

- `All columns must have numeric data`: `from_pandas` and `from_numpy` require numeric inputs; encode categoricals first.
- `Input contains NaN, infinity or a value too large for ...`: clean the input before calling NOTEARS.
- `DAG must have at least 2 nodes`: increase the feature count before generating a synthetic structure.
- `Failed to converge. Consider increasing max_iter.`: raise `max_iter`, reduce the model size, or add stronger tabu constraints.
- `use_gpu=True` does not guarantee CUDA use; the code falls back to CPU when torch cannot see a CUDA device.

## Bayesian-network failures

- `The given structure has ... separated graph components`: connect the graph before building `BayesianNetwork`.
- `The given structure is not acyclic`: remove the cycle before calling `BayesianNetwork`.
- `The data does not cover all the features found in the Bayesian Network`: fit node states from a dataframe that includes every node.
- `Bayesian Network does not contain any CPDs`: call `fit_cpds` or `fit_node_states_and_cpds` before inference.
- `Variable names must match ^[0-9a-zA-Z_]+$`: rename nodes before creating `InferenceEngine`.
- `The cpd for the provided observation must sum to 1` or `must be between 0 and 1`: validate the intervention distribution before `do_intervention`.
- `BayesianNetworkClassifier` requires matching keys in `discretiser_alg` and `discretiser_kwargs`; it also expects a discrete target.

## Discretization failures

- `... is not a recognised method`: use one of `uniform`, `quantile`, `outlier`, `fixed`, or `percentiles`.
- `method expects num_buckets`: provide `num_buckets` for `uniform` or `quantile`.
- `method expects outlier_percentile`: provide a value in `[0, 0.5)` for the outlier method.
- `numeric_split_points must be monotonically increasing`: sort the fixed split points before passing them in.
- `MDLPSupervisedDiscretiserMethod` raises `ImportError`: install the optional package and ensure the build toolchain is available.

## Synthetic-data and transform failures

- `Unknown graph type ...` or `Unknown inter-slice graph type ...`: choose one of the documented graph types for the generator you are using.
- `DAG must have at least 2 nodes`: `generate_structure` cannot create a one-node graph.
- `All inputs must have the same columns and same types`: keep the time-series inputs consistent before using `DynamicDataTransformer`.
- `Index for dataframe must be provided in increasing order`: sort the time-series index before fitting the transformer.
- `All columns must have numeric data`: encode non-numeric time-series columns before calling the transformer.
- `Unsupported variable type ...`: use one of the types accepted by `VariableFeatureMapper` (`binary`, `categorical`, `continuous`, `count`).

## Debug sequence

1. Confirm the public package imports with `scripts/check_install.py`.
2. Run the smoke script for the workflow you care about.
3. If the smoke script fails, read the matching sub-skill and compare its inputs, required types, and output shapes.
4. If the failure is still unclear, inspect the tiny example in `references/workflows.md` and then retry with a smaller dataset.
