# API reference for MIL and debugging

This reference summarizes the repo-backed APIs to use when an advanced task requires direct MIL, pass pipeline, precision, or debugger control. Keep normal model conversion, artifact prediction, and compression tasks in their dedicated sibling sub-skills.

## MIL Builder and program construction

Primary imports:

```python
import coremltools as ct
from coremltools.converters.mil import Builder as mb
from coremltools.converters.mil import Program, Function
from coremltools.converters.mil.mil import types
```

Decorator-style single-function program:

```python
@mb.program(input_specs=[mb.TensorSpec(shape=(1, 4), dtype=types.fp32)])
def prog(x):
    y = mb.relu(x=x, name="relu")
    y = mb.reduce_mean(x=y, axes=[1], keep_dims=False, name="mean")
    return y
```

Manual program/function construction is useful when input names cannot be represented as Python arguments or when constructing functions incrementally:

```python
prog = Program()
func_inputs = {"x": mb.placeholder(shape=(1, 4))}
with Function(func_inputs) as ssa_fun:
    x = ssa_fun.inputs["x"]
    y = mb.square(x=x, name="square")
    ssa_fun.set_outputs([y])
prog.add_function("main", ssa_fun)
```

Useful Builder facts:

- `mb.program(input_specs=[...])` creates a `Program` with one function named `main` by default.
- `mb.function(input_specs=[...])` creates a MIL function rather than a full program.
- `mb.TensorSpec(shape=..., dtype=...)` describes tensor inputs. Omit `dtype` for default floating-point behavior, or pass a MIL dtype such as `types.fp32`, `types.fp16`, or `types.int32`.
- `mb.StateTensorSpec` and `mb.state_tensor_placeholder` support stateful ML Program construction when paired with compatible deployment targets and Core ML runtime support.
- MIL op calls use named inputs. Python constants passed to op inputs are materialized as MIL `const` ops.
- Printing a program gives a concise IR view with function inputs, op names, inferred shapes, and dtypes.

## Converting MIL programs

`ct.convert` accepts a MIL `Program` directly:

```python
mlmodel = ct.convert(
    prog,
    convert_to="mlprogram",          # or "neuralnetwork"
    minimum_deployment_target=ct.target.iOS16,
    compute_precision=ct.precision.FLOAT32,
)
```

Backend notes:

- `convert_to="mlprogram"` produces a typed ML Program. ML Program intermediates carry explicit tensor dtypes.
- `convert_to="neuralnetwork"` produces a neural network model. Intermediate tensor precision is selected by the Core ML runtime and compute unit.
- Prediction is not a portable conversion check. Core ML prediction is supported on macOS; intermediate-output debugging requires runtime support and may also use remote-device APIs.
- ML Program save/conversion paths rely on native coremltools components such as BlobWriter. If those components are missing or incompatible, conversion or save can fail even though pure Python MIL construction succeeds.

## PassPipeline

`PassPipeline` is exposed at the package top level:

```python
pipeline = ct.PassPipeline.DEFAULT
pipeline.remove_passes({"common::fuse_conv_batchnorm"})
pipeline.set_options("common::const_elimination", {"skip_const_by_size": "1000000"})
mlmodel = ct.convert(prog, pass_pipeline=pipeline)
```

Common entry points:

- `ct.PassPipeline.DEFAULT`: converter default common and cleanup passes.
- `ct.PassPipeline.EMPTY`: no graph passes; useful to isolate pass-caused failures.
- `ct.PassPipeline.CLEANUP`: cleanup-only passes such as constant/dead-code cleanup.
- `ct.PassPipeline.DEFAULT_PRUNING` and `ct.PassPipeline.DEFAULT_PALETTIZATION`: compression-related conversion pipelines; route broader compression work to `optimize-models`.
- `ct.PassPipeline.list_available_pipelines()`: names of predefined pipelines.
- `pipeline.passes`: ordered pass names.
- `append_pass`, `insert_pass`, `remove_pass`, `remove_passes`: mutate pass order.
- `set_options(pass_name, options)`: attach pass-specific options. The pass must also be present in `pipeline.passes` when the pipeline validates.

Pass names are registry keys such as `common::dead_code_elimination`, `common::const_elimination`, and `common::fuse_conv_batchnorm`. Unknown names raise registration errors.

## Deployment compatibility

Deployment targets are available under `ct.target`, including iOS/macOS/watchOS/tvOS aliases. Examples include `ct.target.iOS15`, `ct.target.iOS16`, `ct.target.iOS17`, and `ct.target.iOS18`.

Use `minimum_deployment_target` when you need a reproducible compatibility answer:

```python
mlmodel = ct.convert(prog, convert_to="mlprogram", minimum_deployment_target=ct.target.iOS16)
```

If a feature requires a later specification version, coremltools raises an error explaining that the requested target is too low or that the converted model uses newer features. Resolve by raising the target, changing the backend, or replacing the MIL op/pattern.

## Typed execution and precision controls

ML Programs and neural networks handle intermediate precision differently:

- Neural networks type only model inputs and outputs. Runtime partitioning across CPU/GPU/Neural Engine controls intermediate precision. CPU-only execution is the reliable float32 path for neural networks.
- ML Programs type all intermediates. A float32-typed ML Program is guaranteed to preserve float32 tensor precision; a float16-typed ML Program may run with higher precision where the runtime chooses.
- ML Program conversion defaults commonly favor float16 precision for performance. Use `compute_precision=ct.precision.FLOAT32` for a full float32 model.
- Use `ct.transform.Float16ComputePrecision(...)` when you need selective precision control during conversion.

## Composite and custom operators

Prefer composite operators when an unsupported source op can be represented with existing MIL Builder ops.

TensorFlow composite registration:

```python
from coremltools.converters.mil import Builder as mb
from coremltools.converters.mil import register_tf_op

@register_tf_op
def MyOp(context, node):
    x = context[node.inputs[0]]
    y = mb.relu(x=x, name=node.name)
    context.add(y)
```

PyTorch composite registration:

```python
from coremltools.converters.mil.frontend.torch.torch_op_registry import register_torch_op
from coremltools.converters.mil.frontend.torch.ops import _get_inputs
from coremltools.converters.mil import Builder as mb

@register_torch_op
def my_op(context, node):
    x = _get_inputs(context, node, expected=1)[0]
    y = mb.relu(x=x, name=node.name)
    context.add(y)
```

Use custom MIL operators only when a composite cannot represent the behavior. Custom op registration uses `register_op(..., is_custom_op=True)` and a subclass of `Operation` with an `InputSpec`, `type_domains`, `type_inference`, and `bindings`. Custom layer bindings define `class_name`, `input_order`, static `parameters`, and `description` for the Swift/Core ML side. Custom layers are supported for the neural network backend, not ML Programs.

## Debugging utilities

Stable converter-side utility:

```python
from coremltools.converters.mil.debugging_utils import extract_submodel
submodel = extract_submodel(model, outputs=["output_0"], inputs=["x"])
```

Experimental ML Program utilities live under `coremltools.models.ml_program.experimental.*` and may change:

```python
from coremltools.models.ml_program.experimental.debugging_utils import (
    MLModelInspector,
    MLModelValidator,
    MLModelComparator,
    compute_snr_and_psnr,
    skip_op_by_type,
)
```

Capabilities and constraints:

- `MLModelInspector` exposes intermediate ML Program outputs by modifying a cloned spec. It only supports ML Programs.
- `MLModelValidator` uses the inspector to find operations whose outputs satisfy a failure predicate, including NaN or infinite output helpers.
- `MLModelComparator` compares a reference and target ML Program derived from the same source and walks back to failing operations.
- TorchScript and Torch Export comparators map source Torch modules/nodes to converted Core ML behavior, but require the relevant PyTorch export/tracing support.
- These APIs are asynchronous for output retrieval and depend on prediction/runtime availability. Do not promise they will retrieve outputs on non-macOS environments.
