# Feature Engineering and Utility Troubleshooting

## First Diagnostic Step

Run the bundled import probe from this sub-skill directory or with an absolute script path:

```bash
python scripts/check_optional_utilities.py --json
```

Use `--format text` for human-readable output. The script only imports modules and reports versions or exceptions; it does not download data, run examples, train models, or write project files.

## Selector Import Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'lightgbm'` when importing `GBDTSelector` | GBDT selector depends on LightGBM. | Install or select `FeatureGradientSelector`; do not claim `GBDTSelector` works from core NNI alone. |
| `ModuleNotFoundError` for `torch` when importing `FeatureGradientSelector` | Gradient selector imports torch. | Use `GBDTSelector` if LightGBM is available, or install a compatible torch stack before using gradient selection. |
| Missing `sklearn`, `pandas`, `numpy`, or `scipy` | Gradient selector and examples rely on scientific Python stack. | Install the missing dependency or keep guidance conceptual. |
| `ImportError` from `nni.feature_engineering` but `nni.common.serializer` works | Base feature-engineering package or NNI installation is incomplete. | Recheck the NNI install; use the diagnostic output to identify the first failing import. |

## GBDTSelector Fit Failures

- `AssertionError` from `fit`: one of `lgb_params`, `eval_ratio`, `early_stopping_rounds`, `importance_type`, or `num_boost_round` is missing or falsey. Provide every required keyword argument.
- `AssertionError` from `get_selected_features`: `topk` must be positive.
- LightGBM complains about parameters or early stopping: this selector uses the legacy `lightgbm.train(..., early_stopping_rounds=...)` call style, so newer LightGBM versions may require callbacks or adjusted parameters.
- Poor or misleading features: GBDT importance reflects tree splits or gains, which may not select features best for linear models or non-tree downstream estimators.
- Data split issues: `eval_ratio` is passed to sklearn `train_test_split`; ensure enough samples per class/target and avoid using an evaluation split too small for early stopping.

## FeatureGradientSelector Fit Failures

- `AssertionError: order must be an integer between 1 and 12`: lower `order` to the supported range.
- `AssertionError: only specify one of n_features and max_features at a time`: choose an exact retained count or an elbow-method upper bound, not both.
- `ValueError: No Features selected`: lower `penalty`, set `n_features`, increase epochs, inspect data scaling, or use a less aggressive configuration.
- CUDA errors with `device="cuda"`: switch to `device="cpu"` unless the user has verified a compatible torch/CUDA stack.
- NaN loss warnings: the implementation retries with double precision in some paths; if the issue persists, check for NaN/Inf in `X` or `y`, extreme scaling, unsuitable `learning_rate`, or inconsistent labels.
- Empty or incorrect groups: `groups` must align to feature columns with shape `[n_features]`; use hard grouping only when selecting any member should select all group members.
- sklearn pipeline misuse: call `fit` before `transform`, and remember `get_support(indices=True)` returns selected indices while `get_support()` returns a boolean mask.

## Serializer and Trace Problems

| Symptom | Explanation | Recovery |
| --- | --- | --- |
| Deserialized object loses traceability | Some traced function results recover plain values rather than traceable wrappers. | Trace the class or factory that constructs the reusable object, not only a function that returns a primitive. |
| Large cloudpickle payload or `PayloadTooLarge` | The object cannot be represented by import path plus args and falls back to pickling. | Prefer importable top-level classes/functions with explicit constructor args, or adjust `pickle_size_limit` intentionally. |
| Import path error on `nni.load` | The serialized symbol path cannot be imported in the current environment. | Ensure the class/function is installed and importable by the same dotted path; avoid local nested definitions for portable payloads. |
| Constructor side effects happen on load | `nni.load` re-instantiates traced classes/functions. | Do not trace constructors that download datasets, start training, open services, or mutate global state. |
| `None` return behaves unexpectedly under `nni.trace` | Traced functions returning `None` can produce an empty traceable object. | Avoid tracing side-effect-only functions when downstream code checks `is None`. |

Use NNI serializer for configuration transfer and reproducible construction inside NNI workflows, not as durable archival storage across versions.

## Concrete Trace Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'torch'` | Concrete trace is PyTorch-only. | Install torch or choose non-tracing utility guidance. |
| Output changes when input container length changes | Concrete trace flattened loops observed from dummy inputs. | Trace with representative inputs, avoid dynamic container-size assumptions, or keep the logic outside the traced graph. |
| Wrong branch after tracing | Concrete trace recorded the branch taken by dummy inputs. | Use dummy inputs that match deployment branch, refactor dynamic Python control flow, or use leaf wrappers. |
| Failure around `is`, `is not`, `in`, or `not in` | Operator/function patching may need source-file-backed functions and compatible options. | Keep `use_operator_patch=True`, provide functions from importable files, and consider leaf functions/classes for hard cases. |
| Custom classes or model outputs cannot be traced | The tracer does not know how to represent the class. | Add `autowrap_leaf_class`, `autowrap_leaf_function`, `leaf_module`, or `fake_middle_class` as appropriate. |
| Graph instability with random/control-flow behavior | Traced graph changes across passes. | Set deterministic inputs and state; use `trace_twice=True` to detect instability. |
| Device or memory errors | Dummy inputs/model are too large or GPU memory is constrained. | Use smaller representative inputs, move to CPU, or set `cpu_offload=True` when acceptable. |

## Graph, FLOP, and Profiler Problems

- `build_module_graph` and `build_graph` use PyTorch tracing; dynamic Python branches are not fully represented unless they are visible to tracing.
- `build_graph` may require TensorBoard protobuf packages to consume or visualize the returned graph data.
- `flop_count` and `counter_pass` require representative tensor inputs and only count mapped operations; unsupported ops may show zero or incomplete FLOPs.
- `counter_pass(..., verbose=True)` calls `tabulate`; if `tabulate` is missing, use non-verbose output or install it.
- Do not use these utility estimates as proof of compression speedup, NAS quality, or production latency without task-specific benchmarking.

## Boundary Checks

- If the user asks to launch an NNI experiment around feature-generation search, use `../hpo-experiments/` for experiment/trial/tuner/training-service details.
- If the user asks to trace a NAS evaluator or serialize a NAS model space, use this sub-skill for serializer facts and `../nas/` for NAS workflow ownership.
- If the user asks to trace or profile as part of pruning speedup or quantization export, use this sub-skill for standalone trace caveats and `../model-compression/` for compression ownership.
