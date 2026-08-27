# Advanced Backend Choices

This reference distills Hummingbird's advanced backend behavior for already-trained traditional ML models. It focuses on backend choice, `test_input`, CUDA, and TVM. For basic conversion syntax, use the core conversion sub-skill; for detailed ONNX model I/O, use the ONNX sub-skill.

## Backend aliases and runtime availability

Hummingbird builds its backend alias map at import time from packages currently importable in the Python environment.

| User backend string | Canonical backend | Availability condition | Main use |
| --- | --- | --- | --- |
| `"torch"` | `torch` | PyTorch import succeeds | Default PyTorch container; simplest CPU/GPU path. |
| `"pytorch"` | `torch` | PyTorch import succeeds | Compatibility alias for PyTorch output. |
| `"torch.jit"` | `torch.jit` | PyTorch import succeeds | TorchScript/traced model for JIT/deployment scenarios. |
| `"torchscript"` | `torch.jit` | PyTorch import succeeds | Human-friendly alias for TorchScript. |
| `"onnx"` | `onnx` | ONNX Runtime support is importable | ONNX backend/export path; route detailed I/O to the ONNX sub-skill. |
| `"tvm"` | `tvm` | TVM import succeeds | TVM-compiled model with stricter shape and environment constraints. |

If the alias is absent from the map, conversion fails as a missing backend rather than falling back automatically.

## `test_input` requirements

`test_input` is representative input data used for tracing and shape inference. Prefer a small `numpy.ndarray` with the same column count and dtype family as production data. Multiple inputs can be supplied as tuples of arrays, and pandas DataFrames are normalized into columnar inputs when pandas is available.

| Target situation | Is `test_input` required? | Reasoning and notes |
| --- | --- | --- |
| `backend="torch"` from sklearn-style source | Usually optional | The default PyTorch path can often convert without tracing input, unless the source model family itself needs feature inference. |
| `backend="torch.jit"` / `"torchscript"` from non-ONNX source | Yes | TorchScript tracing needs representative inputs. |
| `backend="onnx"` from non-ONNX source | Yes | Export/tracing needs representative inputs. Route ONNX-specific details to the ONNX sub-skill. |
| `backend="tvm"` | Yes | TVM compilation is shape-specialized and requires representative inputs. |
| ONNX-ML source model to advanced backends | Often still provide it | Some ONNX schema paths can infer test input, but explicit representative input is more reliable and avoids unsupported schema/type inference cases. |

The number of rows in `test_input` is not just a sample count for traced/compiled backends: it becomes the tracing batch size for TorchScript and the compiled batch shape for TVM.

## CUDA and GPU execution

Hummingbird exposes two common GPU patterns for PyTorch-family outputs:

```python
from hummingbird.ml import convert

hb_model = convert(trained_model, "torch", test_input=X_small, device="cuda")
# or convert on CPU first, then move the wrapped PyTorch model/container:
hb_model = convert(trained_model, "torch", test_input=X_small)
hb_model.to("cuda")
```

Use CUDA only after checking the actual PyTorch build and device visibility:

- `torch.cuda.is_available()` must be true.
- `torch.cuda.device_count()` should be at least one.
- `torch.version.cuda` should be non-null for CUDA PyTorch builds.
- A CPU-only PyTorch wheel cannot run CUDA Hummingbird inference; reinstalling PyTorch, if desired, must match the user's CUDA runtime/driver and platform.

The `device` argument is documented for PyTorch-family backends and TVM, and accepts PyTorch-style device strings such as `"cpu"` or `"cuda"`. Do not claim GPU verification from CPU-only conversion checks.

## TorchScript selection

Choose TorchScript when the user asks for:

- a traced model/container,
- TorchServe-style serving,
- deployment through PyTorch JIT mechanisms,
- lower Python overhead after conversion,
- compatibility with Hummingbird save/load paths for TorchScript containers.

Minimal pattern:

```python
from hummingbird.ml import convert

hb_ts = convert(trained_model, "torch.jit", test_input=X_small)
pred = hb_ts.predict(X_eval)
```

`"torchscript"` and `"torch.jit"` route to the same canonical backend when PyTorch is available.

## TVM selection

Choose TVM only when all of these are true:

1. TVM is already importable in the runtime environment.
2. The Python version is compatible with the TVM build in use; Hummingbird's documented package guidance says TVM only works through Python 3.10.
3. The user accepts compilation overhead and fixed-shape behavior.
4. A representative `test_input` with the intended shape is available.
5. GPU TVM is requested only if the installed TVM build and visible CUDA stack support it.

Minimal CPU TVM pattern:

```python
from hummingbird.ml import convert
from hummingbird.ml import constants

hb_tvm = convert(
    trained_model,
    "tvm",
    test_input=X_batch,
    extra_config={constants.TVM_MAX_FUSE_DEPTH: 30},
)
pred = hb_tvm.predict(X_batch)
```

GPU TVM uses the `device` argument, but should be treated as unverified unless the TVM build and CUDA device have both been checked:

```python
hb_tvm_gpu = convert(trained_model, "tvm", test_input=X_batch, device="cuda")
```

## TVM shape contract

A TVM container produced by `convert(...)` is compiled for the shape of `test_input`. A different prediction batch size can fail unless you use one of these approaches:

- call `convert_batch(...)` so prediction proceeds in batch-sized chunks, optionally with a remainder model;
- set `extra_config={constants.TVM_PAD_INPUT: True}` to pad shorter batch dimensions with zeros, accepting a possible performance penalty;
- recompile with a new representative `test_input` shape.

The TVM backend also accepts `constants.TVM_MAX_FUSE_DEPTH`; Hummingbird defaults the Relay fuse depth to 50. Use smaller values such as 30 or 10 when a local TVM compilation is taking too long on a representative smoke input.

## Boundary with benchmarks

Hummingbird includes benchmark programs for paper-scale experiments, but complete benchmark suites can take days. Treat them as reference designs for measurement methodology, not as routine validation to run during a normal repo-skill task. Prefer small conversion parity checks and the backend probe script unless the user explicitly budgets a benchmark run.
