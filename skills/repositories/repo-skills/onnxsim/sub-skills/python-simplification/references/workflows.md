# Workflow Recipes

This file collects the common simplification workflows owned by the
`python-simplification` sub-skill. Use the API or CLI examples below as-is, or
adapt them to the caller's model names and shapes.

## 1) File-to-file simplification

```bash
onnxsim input.onnx output.onnx
```

Add validation and a clearer failure signal:

```bash
onnxsim input.onnx output.onnx 3 --check-rtol 1e-4 --check-atol 1e-5
```

Print a graph diff after simplification:

```bash
onnxsim input.onnx output.onnx 3 --graph-diff
```

## 2) Python `ModelProto` workflow

```python
import onnx
from onnxsim import simplify

model = onnx.load("input.onnx")
model_simp, check = simplify(model)
assert check
onnx.save(model_simp, "output.onnx")
```

Use `check_n` and deterministic input filling when you want the simplifier to
validate the result itself:

```python
model_simp, check = simplify(
    model,
    check_n=3,
    input_fill="arange",
    check_rtol=1e-4,
    check_atol=1e-5,
)
```

## 3) Dynamic shapes

Pin a dynamic model for both simplification and validation:

```python
model_simp, check = simplify(
    model,
    overwrite_input_shapes={"input": [1, 3, 224, 224]},
    test_input_shapes={"input": [1, 3, 224, 224]},
    check_n=3,
)
```

CLI equivalent:

```bash
onnxsim input.onnx output.onnx 3 \
  --overwrite-input-shape input:1,3,224,224 \
  --test-input-shape input:1,3,224,224
```

Notes:

- `overwrite_input_shapes` pins the model shape used for simplification.
- `test_input_shapes` gives the checker concrete dimensions to generate.
- If only the batch dimension is dynamic, the checker treats it as `1` unless
  you override it.
- If a later dimension is dynamic, you must supply a full `test_input_shape`.

## 4) Validation inputs and fill modes

Use caller-supplied tensors when you already have them:

```python
import numpy as np
model_simp, check = simplify(
    model,
    check_n=3,
    input_data={"input": np.load("input.npy")},
)
```

Use a reproducible fill pattern for the random checker inputs:

```python
model_simp, check = simplify(model, check_n=3, input_fill="zeros")
model_simp, check = simplify(model, check_n=3, input_fill="ones")
model_simp, check = simplify(model, check_n=3, input_fill="arange")
```

The supported fill choices are `random`, `ones`, `zeros`, and `arange`.

## 5) Provider selection and CUDA shortcut behavior

CPU is the default provider for constant folding.

```python
model_simp, check = simplify(model, providers=["CPUExecutionProvider"])
```

GPU-then-CPU folding:

```python
model_simp, check = simplify(
    model,
    providers=["CUDAExecutionProvider", "CPUExecutionProvider"],
)
```

Provider options tuples are passed through unchanged:

```python
model_simp, check = simplify(
    model,
    providers=[("CUDAExecutionProvider", {"device_id": 1}), "CPUExecutionProvider"],
)
```

CLI shortcut:

```bash
onnxsim input.onnx output.onnx --cuda
```

Important provider rule:

- `onnxruntime` is optional.
- Non-CPU providers require `onnxruntime` and the correct provider build.
- The helper validates providers up front; if a provider is unavailable, the
  simplifier raises `ValueError` and lists the available providers.

## 6) External data and large tensors

When the output model is too large for a normal inline save, use external data:

```bash
onnxsim input.onnx output.onnx --save-as-external-data
```

For very large models, keep the size guard on the folding step:

```bash
onnxsim input.onnx output.onnx --no-large-tensor 1MB
```

A bare `--no-large-tensor` flag uses the very conservative `1KB` threshold.
This avoids baking enormous intermediates from ops such as `Tile`,
`ConstantOfShape`, or `Expand`.

## 7) Target opset conversion

Convert before simplification when the caller wants a different default-domain
opset:

```python
model_simp, check = simplify(model, target_opset_version=18)
```

```bash
onnxsim input.onnx output.onnx --target-opset 18
```

The conversion happens before simplification, so redundant nodes introduced by
conversion can still be cleaned up.

## 8) Function inlining

Inline only local model-defined functions when you want the optimizer and
shape inference to see through them:

```python
model_simp, check = simplify(model, inline_functions=True)
```

Schema-defined ONNX built-ins are left alone.

## 9) Custom operator schema import

If the model uses custom operators, register their schemas in Python `onnx`
first:

```python
import onnx
from onnx import defs

# defs.register_schema(my_schema)
model_simp, check = simplify(model)
```

Simplification imports Python-registered schemas automatically.

Turn that off only when you need to leave the onnxsim registry untouched:

```python
model_simp, check = simplify(model, import_custom_schemas=False)
```

CLI equivalent:

```bash
onnxsim input.onnx output.onnx --skip-schema-import
```

If you need the bridge explicitly, call `onnxsim.import_onnx_schemas()` before
simplifying.

## 10) Output validation and graph diff

Recommended validation loop for a caller who wants an explicit check:

```python
import onnx
from onnxsim import backend, simplify

model = onnx.load("input.onnx")
model_simp, check = simplify(model, check_n=3, input_fill="arange")
assert check

inputs = {"input": ...}
orig = backend.run_model(model, inputs)
opt = backend.run_model(model_simp, inputs)
```

For a human-readable structural diff, enable `--graph-diff` on the CLI or call
`onnxsim.model_info.print_graph_diff(model, model_simp)` in Python.

## 11) Tiny helper smoke

The bundled helper script covers a safe local smoke test without any downloads:

```bash
python scripts/simplify_tiny_model.py --help
python scripts/simplify_tiny_model.py --check-n 3 --input-fill arange --print-summary
python scripts/simplify_tiny_model.py --output tiny-simplified.onnx
```
