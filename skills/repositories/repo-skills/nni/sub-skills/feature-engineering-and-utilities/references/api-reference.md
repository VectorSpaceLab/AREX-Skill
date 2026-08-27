# Feature Engineering and Utility API Reference

## Import Map

| Capability | Primary API | Optional dependencies |
| --- | --- | --- |
| Base selector contract | `nni.feature_engineering.feature_selector.FeatureSelector` | none beyond NNI required deps |
| GBDT feature selection | `nni.algorithms.feature_engineering.gbdt_selector.GBDTSelector` | `lightgbm`, `sklearn` |
| Gradient feature selection | `nni.algorithms.feature_engineering.gradient_selector.FeatureGradientSelector` | `torch`, `numpy`, `pandas`, `scikit-learn`, `scipy` |
| Trace serialization | `nni.trace`, `nni.dump`, `nni.load`; `nni.common.serializer` | NNI required deps include `json_tricks` and `cloudpickle` |
| Concrete tracing | `nni.common.concrete_trace_utils.concrete_trace`, `ConcreteTracer` | `torch` |
| JIT graph utilities | `nni.common.graph_utils.build_module_graph`, `build_graph`, `TorchModuleGraph` | `torch`; TensorBoard protobuf support for `build_graph` output use |
| FLOP utilities | `nni.common.concrete_trace_utils.flop_utils.flop_count` | `torch` |
| FX profiler pass | `nni.common.concrete_trace_utils.counter.counter_pass`, `GraphCounter` | `torch`; `tabulate` only for verbose summary formatting |

## FeatureSelector Base Contract

`FeatureSelector` stores `selected_features_`, `X`, and `y` and defines the minimal contract for custom selectors.

- `fit(X, y, **kwargs)`: records tabular training inputs shaped `[n_samples, n_features]` and targets shaped `[n_samples]`.
- `get_selected_features()`: returns `selected_features_` as the selected feature indices.
- For sklearn compatibility, custom selectors should also implement `get_params`, `set_params`, `get_support`, `transform`, and `inverse_transform` through `BaseEstimator` and `SelectorMixin` patterns.

## GBDTSelector

Import path:

```python
from nni.algorithms.feature_engineering.gbdt_selector import GBDTSelector
```

`GBDTSelector.fit(X, y, **kwargs)` requires all of these keyword arguments:

| Argument | Meaning |
| --- | --- |
| `lgb_params` | LightGBM training parameters such as objective, metrics, leaves, learning rate, and sampling fractions. |
| `eval_ratio` | Fraction of data split into validation/evaluation data by sklearn `train_test_split`. |
| `early_stopping_rounds` | LightGBM early stopping setting. |
| `importance_type` | `"gain"` or `"split"` for LightGBM feature importance. |
| `num_boost_round` | Number of boosting rounds passed to `lightgbm.train`. |

`GBDTSelector.get_selected_features(topk)` returns the top `topk` feature indices by descending LightGBM feature importance. `topk` must be positive.

Use this selector for fast tree-based baselines and LightGBM-style feature ranking. Warn when missing LightGBM, when the installed LightGBM API differs from the legacy `early_stopping_rounds` call style, or when sparse/dense data needs conversion for the user’s LightGBM version.

## FeatureGradientSelector

Import path:

```python
from nni.algorithms.feature_engineering.gradient_selector import FeatureGradientSelector
```

Constructor highlights:

| Argument | Meaning |
| --- | --- |
| `order=4` | Interaction order; must be between 1 and 12. Higher order can increase runtime. |
| `penalty=1` | Regularization multiplier. Lowering it can recover from no features selected. |
| `n_features=None` | Exact number of selected features. Mutually exclusive with `max_features`. |
| `max_features=None` | Upper bound for elbow-method feature count recommendation. Mutually exclusive with `n_features`. |
| `learning_rate=1e-1` | Gradient search learning rate. |
| `init="zero"` | Score initialization. Supported values include `zero`, `on`, `off`, `onhigh`, `offhigh`, and `sklearn`. |
| `n_epochs=1` | Number of epochs. More epochs can improve results but cost more. |
| `batch_size=1000` | Rows processed at a time. Clamped to data size during fitting. |
| `target_batch_size=1000` | Rows accumulated for gradient estimates. |
| `classification=True` | Set `False` for regression. |
| `ordinal=False` | Use only with classification tasks that are ordinal. |
| `balanced=True` | Weight classes equally for classification. |
| `preprocess="zscore"` | Preprocess mode; `zscore` or `center`. |
| `soft_grouping=False` | Whether groups encourage sparsity rather than hard group selection. |
| `device="cpu"` | `cpu` or `cuda`, depending on local torch/CUDA readiness. |

Methods:

- `fit(X, y, groups=None)`: fits in one batch workflow; accepts NumPy arrays or pandas objects and optional group ids shaped `[n_features]`.
- `partial_fit(X, y, n_classes=None, groups=None)`: supports repeated fitting over chunks; pass `n_classes` on the first call when the batch may not include all classes.
- `get_selected_features()`: returns selected feature indices after fitting.
- `transform(X)`: returns selected columns and raises `ValueError` if no features are selected.
- `get_support(indices=False)`: returns a boolean mask or selected indices.
- `set_n_features(n, groups=None)` and `set_top_percentile(percentile, groups=None)`: adjust the selected count after scores are fitted.

Use this selector for sklearn pipelines, wide tabular data, possible high-order interactions, and grouped feature constraints. Do not set both `n_features` and `max_features`.

## Serializer and Trace APIs

Common imports:

```python
import nni
from nni.common.serializer import is_traceable, is_wrapped_with_trace
```

Core APIs:

| API | Use |
| --- | --- |
| `nni.trace(cls_or_func=None, *, kw_only=True, inheritable=False)` | Wrap an importable class or function so its construction arguments are preserved. |
| `nni.dump(obj, fp=None, *, use_trace=True, pickle_size_limit=4096, allow_nan=True, **kwargs)` | Serialize nested objects to JSON text or a file-like target. |
| `nni.load(string=None, *, fp=None, preserve_order=False, ignore_comments=True, **kwargs)` | Deserialize from a JSON string or file-like target. |
| `is_traceable(obj, must_be_instance=False)` | Check whether an object implements the NNI traceable interface. |
| `is_wrapped_with_trace(cls_or_func)` | Check whether a class or function has already been wrapped with `nni.trace`. |

Traceable objects expose `trace_symbol`, `trace_args`, `trace_kwargs`, `trace_copy()`, and `get()`. The serializer can fall back to `cloudpickle`; keep `pickle_size_limit` in mind for large or local objects.

## Concrete Trace APIs

Import path:

```python
from nni.common.concrete_trace_utils import ConcreteTracer, concrete_trace
```

`concrete_trace(root, concrete_args, *, use_operator_patch=True, operator_patch_backlist=None, forward_function_name="forward", check_args=None, autowrap_leaf_function=None, autowrap_leaf_class=None, leaf_module=None, fake_middle_class=None, dce=True, cpu_offload=False, trace_twice=False)` returns a `torch.fx.GraphModule`.

Important semantics:

- `root` is a `torch.nn.Module` or callable.
- `concrete_args` are representative dummy inputs as a dict or tuple.
- `check_args` runs a cheap equivalence check by calling both original and traced functions.
- `autowrap_leaf_function` and `autowrap_leaf_class` extend `ConcreteTracer.default_autowrap_leaf_function` and `ConcreteTracer.default_autowrap_leaf_class` when functions/classes should be opaque leaves.
- `trace_twice=True` asserts graph stability across two tracing passes.
- `dce=True` eliminates dead code after tracing.

Concrete trace executes Python and records the observed path. It can trace many cases symbolic FX cannot, but it cannot infer all future dynamic control-flow branches.

## Graph and Profiler APIs

- `build_module_graph(model, dummy_input)` returns `TorchModuleGraph`; it traces a PyTorch model with `torch.jit.trace` or uses an already traced model inside `TorchGraph`.
- `build_graph(model, dummy_input, verbose=False)` returns `(graph_def, stepstats)` for TensorBoard-compatible graph visualization.
- `flop_count(module_or_callable, *args, verbose=False, forward_only=True, **kwargs)` returns forward FLOPs or `(forward_flops, backward_flops)` when `forward_only=False`.
- `counter_pass(module, *args, verbose=False, by_type=False)` runs an FX `GraphModule` and returns dictionaries for `flops` and `params` by node name or module type.

These helpers require representative tensor inputs and are best used as inspection aids, not as authoritative benchmark measurements.
