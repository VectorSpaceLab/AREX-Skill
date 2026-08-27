# Hummingbird API Overview

## Purpose

Read this when you need a compact package map before choosing a sub-skill. Keep detailed workflow decisions in the nearest sub-skill reference.

## Package identity

| Item | Value |
| --- | --- |
| Distribution | `hummingbird-ml` |
| Import package | `hummingbird`, `hummingbird.ml` |
| Version captured for this skill | `0.4.12` |
| Main APIs | `convert`, `convert_batch`, `load` |
| Container exports | `TorchContainer`, `ONNXContainer`, `TVMContainer` |

## Main conversion APIs

```python
from hummingbird.ml import convert, convert_batch, load, constants

hb_model = convert(model, backend, test_input=None, device="cpu", extra_config={})
hb_batch_model = convert_batch(model, backend, test_input, remainder_size=0, device="cpu", extra_config={})
loaded = load("saved_model", digest=digest)  # or override_flag=True only for trusted artifacts
```

Important rules:

- `model` must be fitted/trained for normal scikit-learn estimators.
- `backend` is a string and is normalized case-insensitively.
- `test_input` is important for tracing/export paths and for source models where Hummingbird cannot infer input shape/features.
- `extra_config` accepts constants from `hummingbird.ml.constants`; prefer constants over raw strings when writing robust code.
- `convert_batch` creates a container specialized for batch-by-batch prediction where output input row counts must match `test_input.shape[0] * k + remainder_size`.

## Backend aliases

| Alias | Target | Notes |
| --- | --- | --- |
| `"torch"`, `"pytorch"` | PyTorch container | Default choice for CPU parity and lowest-friction local validation. |
| `"torch.jit"`, `"torchscript"` | TorchScript container | Requires representative `test_input` for tracing. Useful for deployment-style artifacts. |
| `"onnx"` | ONNX Runtime container/model | Requires ONNX extras such as `onnxruntime`; representative `test_input` is strongly recommended. |
| `"tvm"` | TVM container | Optional; requires a prepared TVM environment and fixed-shape expectations. |

The active backend map depends on installed optional packages. If a backend alias is missing, run `scripts/check_hummingbird_env.py` and read the relevant troubleshooting reference.

## Supported source families

- Core: scikit-learn estimators, transformers, and pipelines whose operators appear in Hummingbird's support map.
- Optional: LightGBM, XGBoost, Prophet, SparkML, and ONNX-ML inputs. These need extra dependencies and may have additional `test_input`, schema, JVM, or system-library requirements.

## Common `extra_config` constants

| Constant | String value | Primary owner |
| --- | --- | --- |
| `constants.TREE_IMPLEMENTATION` | `"tree_implementation"` | tree strategy (`gemm`, `tree_trav`, `perf_tree_trav`) |
| `constants.TREE_OP_PRECISION_DTYPE` | `"tree_op_precision_dtype"` | tree threshold/leaf dtype (`float32` or `float64`) |
| `constants.N_THREADS` | `"n_threads"` | backend thread count for scoring/session creation |
| `constants.BATCH_SIZE` | `"batch_size"` | batch partitioning option for inference paths |
| `constants.INPUT_NAMES` | `"input_names"` | named inputs for columnar/multiple-input conversion |
| `constants.OUTPUT_NAMES` | `"output_names"` | named outputs |
| `constants.MAX_STRING_LENGTH` | `"max_string_length"` | string feature encoding size for string categorical inputs |
| `constants.ONNX_TARGET_OPSET` | `"onnx_target_opset"` | ONNX export target opset |
| `constants.ONNX_OUTPUT_MODEL_NAME` | `"onnx_model_name"` | ONNX output model name |
| `constants.TVM_MAX_FUSE_DEPTH` | `"tvm_max_fuse_depth"` | TVM Relay fusion limit |
| `constants.TVM_PAD_INPUT` | `"tvm_pad_prediction_inputs"` | TVM fixed-shape padding behavior |

## Prediction methods by container kind

| Source kind | Expected converted methods |
| --- | --- |
| Transformer/preprocessor | `transform(...)` |
| Regressor | `predict(...)` |
| Classifier | `predict(...)`, often `predict_proba(...)` |
| Anomaly detector | `predict(...)`, `decision_function(...)`, `score_samples(...)` |

Always validate the method the downstream code will actually use.
