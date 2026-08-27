# Feature Engineering and Utility Workflows

## Choose a Feature Selector

1. Confirm the data is tabular: `X` should be shaped `[n_samples, n_features]`, and `y` should be shaped `[n_samples]`.
2. Prefer `GBDTSelector` when the user wants a tree-based baseline, already has or can install LightGBM, and wants feature importance from boosted decision trees.
3. Prefer `FeatureGradientSelector` when the user needs gradient-based search, possible high-order feature interactions, sklearn pipeline compatibility, grouped columns, or very wide tabular data where `n_features` or `max_features` constrains output size.
4. Use the base `FeatureSelector` only as a customization contract: subclass it and implement `fit` plus `get_selected_features`; add sklearn `BaseEstimator` and `SelectorMixin` methods if the selector must plug into sklearn pipelines.
5. If the prompt asks for generated high-order feature exploration rather than selecting existing columns, route the trial/search aspects to `../hpo-experiments/`; this sub-skill can still explain selectors that reduce the resulting feature set.

### GBDTSelector Pattern

Use `nni.algorithms.feature_engineering.gbdt_selector.GBDTSelector` for LightGBM-backed ranking.

```python
from nni.algorithms.feature_engineering.gbdt_selector import GBDTSelector

selector = GBDTSelector()
selector.fit(
    X_train,
    y_train,
    lgb_params={"boosting_type": "gbdt", "objective": "regression", "metric": {"l2", "l1"}},
    eval_ratio=0.1,
    early_stopping_rounds=10,
    importance_type="gain",
    num_boost_round=100,
)
selected = selector.get_selected_features(topk=10)
```

Use `importance_type="gain"` when split gain is more meaningful than raw split count, and `importance_type="split"` when the user wants count-based importance. Keep `topk` positive and no larger than the number of available columns.

### FeatureGradientSelector Pattern

Use `nni.algorithms.feature_engineering.gradient_selector.FeatureGradientSelector` for gradient-based selection and sklearn integration.

```python
from nni.algorithms.feature_engineering.gradient_selector import FeatureGradientSelector

selector = FeatureGradientSelector(n_epochs=1, n_features=10, device="cpu")
selector.fit(X_train, y_train, groups=groups_or_none)
selected = selector.get_selected_features()
X_reduced = selector.transform(X_train)
```

Use `n_features` for an exact number of retained columns, or `max_features` when the selector should recommend a count with its elbow method. Do not set both at once. Use `classification=False` for regression and `device="cuda"` only when the local environment has a compatible torch/CUDA stack.

## Serializer and Trace Workflow

Use `nni.trace`, `nni.dump`, and `nni.load` when NNI needs to preserve how an object was constructed rather than only its current values.

1. Wrap classes or functions before instantiating/calling them: `optimizer = nni.trace(torch.optim.Adam)(model.parameters(), lr=0.001)`.
2. Serialize with `payload = nni.dump(obj)`; deserialize with `obj = nni.load(payload)`.
3. Check traceability with `nni.common.serializer.is_traceable(obj)` when a downstream NNI workflow requires traced optimizers, schedulers, trainers, datasets, or callable factories.
4. Use `nni.dump(..., pickle_size_limit=-1)` only when the object cannot be represented by import path plus arguments and a larger cloudpickle payload is acceptable.
5. Avoid using NNI serializer as long-term storage: the serializer is intended for process-to-process transfer and its format can change between NNI releases.

Good candidates are importable functions/classes with stable constructor arguments. Poor candidates include lambdas, local nested classes/functions, open file handles, non-deterministic generators, or objects whose constructor causes downloads/training/side effects.

## Concrete Trace Workflow

Use `nni.common.concrete_trace_utils.concrete_trace` when `torch.fx.symbolic_trace` is too weak for a PyTorch model/function and the user can provide representative dummy inputs.

```python
from nni.common.concrete_trace_utils import concrete_trace

traced = concrete_trace(model, {"x": dummy_input}, check_args={"x": check_input})
```

1. Require `torch` and a `torch.nn.Module` or callable root.
2. Put the module in a safe state for tracing; `concrete_trace` temporarily calls `eval()` and restores training mode afterward.
3. Provide `concrete_args` as a dict keyed by argument name or as a tuple of positional dummy inputs.
4. Use `check_args` when a cheap correctness check is available and input/output equality is meaningful.
5. Use `autowrap_leaf_function`, `autowrap_leaf_class`, `leaf_module`, or `fake_middle_class` when a function/class/module must remain opaque rather than be traced through.
6. Use `cpu_offload=True` only to reduce tracing memory when CPU/GPU movement is acceptable.

Concrete tracing records the structure observed from the dummy inputs. Branches and loops over Python containers can be flattened to the observed length or branch, so traced behavior may not generalize to different container sizes or control-flow paths.

## Graph and Profiler Utility Workflow

Use these utilities only after confirming `torch` is importable.

- `nni.common.graph_utils.build_module_graph(model, dummy_input)` builds a `TorchModuleGraph` from `torch.jit.trace` and is useful for model-topology inspection.
- `nni.common.graph_utils.build_graph(model, dummy_input, verbose=False)` returns TensorBoard-compatible graph data and step stats from a traced PyTorch model.
- `nni.common.concrete_trace_utils.flop_utils.flop_count(module_or_callable, *args, verbose=False, forward_only=True, **kwargs)` estimates FLOPs for a module or callable with representative tensor inputs.
- `nni.common.concrete_trace_utils.counter.counter_pass(graph_module, *args, verbose=False, by_type=False)` profiles a `torch.fx.GraphModule`, returning FLOP and parameter-size dictionaries by node or module type.

Prefer these utilities for static inspection, debugging, and lightweight profiling. Do not present them as compression speedup, NAS evaluation, or benchmark-quality measurement tools unless another sub-skill owns that higher-level workflow.

## Optional Dependency Diagnosis Workflow

Run the bundled diagnostic before advising installation or code changes:

```bash
python scripts/check_optional_utilities.py --json
```

Interpret results by capability:

- `nni.common.serializer` importable: trace serialization helpers should be available through `nni.trace`, `nni.dump`, and `nni.load`.
- `nni.feature_engineering` importable but selector modules failing: base feature selector may be available, while concrete selectors likely need optional dependencies.
- `lightgbm` missing: `GBDTSelector` cannot import or fit.
- `torch` missing: `FeatureGradientSelector`, concrete trace, graph utilities, FLOP utilities, and profiler utilities cannot be used.
- `sklearn`, `pandas`, `numpy`, or `scipy` missing: gradient feature selection and examples may fail even if base NNI imports work.
