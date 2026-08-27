# API reference for core conversion

## Imports

```python
import hummingbird.ml
from hummingbird.ml import convert, convert_batch, constants, backends
from hummingbird.ml.exceptions import MissingBackend, MissingConverter
```

`hummingbird.ml.backends` exposes the backend names currently registered in the active environment. The map is environment-dependent: a backend appears only when its required packages are importable.

## Main entry points

| Function | Signature | Use when |
|---|---|---|
| `convert` | `convert(model, backend, test_input=None, device="cpu", extra_config={})` | Ordinary one-shot conversion of a fitted source model to a target backend. |
| `convert_batch` | `convert_batch(model, backend, test_input, remainder_size=0, device="cpu", extra_config={})` | Batch-by-batch inference where input row counts follow `test_input.shape[0] * k + remainder_size`. |

Both functions return a Hummingbird container by default. The container exposes scikit-learn-like inference methods where supported by the converted operator, such as `predict`, `predict_proba`, `transform`, `decision_function`, and `score_samples`.

## Arguments

| Argument | Meaning | Practical guidance |
|---|---|---|
| `model` | Fitted source model. Core use is scikit-learn-style estimators. | Fit the estimator before conversion. Unfitted sklearn estimators can raise `sklearn.exceptions.NotFittedError`. |
| `backend` | Target backend string. | Must be a string. Backend matching is case-insensitive after normalization. Unsupported or unavailable backends raise `MissingBackend`. |
| `test_input` | Representative input used for tracing/compilation and shape inference. | Required for `convert_batch`; required by TorchScript, TVM, and sklearn-to-ONNX backend conversion; recommended whenever shape-sensitive behavior matters. |
| `device` | Device passed to torch-family and TVM backends. | Use `"cpu"` for verified core workflows. Route CUDA/GPU decisions to `advanced-backends-and-performance`. |
| `extra_config` | Dictionary of converter-specific options. | Use documented `hummingbird.ml.constants` keys. Pass a fresh dict when reusing configs across calls. |
| `remainder_size` | `convert_batch` leftover row count. | Choose the remainder such that evaluation input sizes equal `batch_size * k + remainder_size`, where `batch_size == test_input.shape[0]`. |

## Backend aliases and requirements

| Input backend string | Normalized target | Requirement notes |
|---|---|---|
| `"torch"` | PyTorch | Requires PyTorch. Good default for CPU smoke/parity. |
| `"pytorch"` | PyTorch | Compatibility alias for `"torch"`. |
| `"torch.jit"` | TorchScript | Requires PyTorch and `test_input`. |
| `"torchscript"` | TorchScript | Alias for `"torch.jit"`; requires `test_input`. |
| `"onnx"` | ONNX | Requires ONNX-related runtime packages; sklearn source conversion should provide `test_input`. Route output-file/model-I/O details to `onnx-and-model-io`. |
| `"tvm"` | TVM | Requires TVM and `test_input`. Route setup and performance behavior to `advanced-backends-and-performance`. |

Backend names are looked up after lowercasing. A non-string backend, such as an old-style initial-types list passed as the second positional argument, raises `ValueError`.

## Fitted-estimator guard

For recognized sklearn estimator classes, Hummingbird checks that the estimator has already been fitted before parsing it. If the check fails, the conversion raises `sklearn.exceptions.NotFittedError` before a Hummingbird container is created.

Recovery pattern:

```python
from sklearn.utils.validation import check_is_fitted

check_is_fitted(skl_model)  # raises before conversion if not fitted
hb_model = convert(skl_model, "torch")
```

If the user wants Hummingbird to train a model, clarify that Hummingbird converts trained traditional ML models; it does not replace the estimator's training step.

## `extra_config` keys most relevant here

Use `hummingbird.ml.constants` rather than string literals when possible.

| Constant | String key | Core use |
|---|---|---|
| `constants.TREE_IMPLEMENTATION` | `"tree_implementation"` | Choose tree conversion implementation, e.g. `"gemm"`, `"tree_trav"`, `"perf_tree_trav"`; route detailed selection to sklearn operator coverage. |
| `constants.TREE_OP_PRECISION_DTYPE` | `"tree_op_precision_dtype"` | Set precision for tree thresholds/leaf values; route precision trade-offs to operator/performance guidance. |
| `constants.CONTAINER` | `"container"` | Defaults to `True`, returning a scikit-learn-style container. Setting `False` is an advanced escape hatch. |
| `constants.INPUT_NAMES` / `constants.OUTPUT_NAMES` | `"input_names"` / `"output_names"` | Name inputs/outputs for compatible conversion paths; route complex schemas to pipeline or ONNX sub-skills. |
| `constants.N_THREADS` | `"n_threads"` | Controls intra-op scoring threads; route tuning to advanced backends/performance. |
| `constants.BATCH_SIZE` | `"batch_size"` | Inference partitioning option distinct from `convert_batch`'s trace batch size; route performance tuning elsewhere. |
| `constants.MAX_STRING_LENGTH` | `"max_string_length"` | String-feature conversion guard; route detailed string/pipeline cases to sklearn operator coverage. |
| `constants.ONNX_OUTPUT_MODEL_NAME` / `constants.ONNX_TARGET_OPSET` | `"onnx_model_name"` / `"onnx_target_opset"` | ONNX output customization; route detailed ONNX workflows to `onnx-and-model-io`. |

## `convert_batch` notes

`convert_batch` stores `remainder_size` in `extra_config` before conversion. If you pass an existing dictionary and then reuse it for ordinary `convert`, create a copy or remove the remainder key first.

```python
cfg = {constants.TREE_IMPLEMENTATION: "gemm"}
hb_batch = convert_batch(model, "torch", X[:8], remainder_size=3, extra_config=dict(cfg))
hb_plain = convert(model, "torch", extra_config=dict(cfg))
```

For ordinary PyTorch inference without fixed shape requirements, start with `convert`. Use `convert_batch` only when the workload or backend needs the fixed batch/remainder behavior.
