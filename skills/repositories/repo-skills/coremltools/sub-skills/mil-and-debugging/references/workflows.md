# MIL and debugging workflows

Use these workflows when the problem is past ordinary conversion and requires direct MIL, pass, precision, or runtime-debugger control.

## 1. Minimal MIL program workflow

Use this to prove that Builder construction, MIL type inference, conversion, and save all work before debugging a larger graph.

```python
import coremltools as ct
from coremltools.converters.mil import Builder as mb
from coremltools.converters.mil.mil import types

@mb.program(input_specs=[mb.TensorSpec(shape=(1, 4), dtype=types.fp32)])
def prog(x):
    scale = mb.const(val=[1.0, 2.0, 3.0, 4.0], name="scale")
    y = mb.mul(x=x, y=scale, name="scaled")
    y = mb.relu(x=y, name="relu")
    return mb.reduce_mean(x=y, axes=[1], keep_dims=False, name="mean")

print(prog)
model = ct.convert(prog, convert_to="mlprogram", compute_precision=ct.precision.FLOAT32)
model.save("mil_smoke.mlpackage")
```

Checklist:

1. Give important ops explicit names so later inspectors and error messages are actionable.
2. Keep input dtypes explicit when investigating precision or integer behavior.
3. Print the MIL program before conversion to verify inferred shape/dtype and inserted constants.
4. Save the model before attempting prediction. Save failures point to backend/native packaging, not source framework conversion.
5. Avoid prediction as the first smoke test unless the environment is known to have a compatible Core ML runtime.

## 2. Conversion failure triage

Classify by stage and then shrink the reproducer.

1. **MIL construction/type inference:** the failure occurs while executing Builder code or printing the program. Check op input names, const values, ranks, symbolic dimensions, and dtypes.
2. **Graph pass:** the MIL program builds, but `ct.convert(..., pass_pipeline=...)` fails. Compare `ct.PassPipeline.EMPTY`, `ct.PassPipeline.CLEANUP`, and the default pipeline.
3. **Backend lowering/save:** conversion reaches MLModel creation or `save`, then fails. Compare `convert_to="mlprogram"` and `convert_to="neuralnetwork"`; ML Program failures may involve BlobWriter/native package support.
4. **Deployment compatibility:** conversion fails only with `minimum_deployment_target`. Raise the target or replace the op/pattern requiring a newer spec.
5. **Runtime/prediction:** conversion and save work, but `predict` or intermediate retrieval fails. This is usually Core ML runtime, compute unit, input name/dtype, or platform availability.

Shrinking sequence:

```python
# 1. Does pure MIL conversion work without common graph rewrites?
model = ct.convert(prog, convert_to="mlprogram", pass_pipeline=ct.PassPipeline.EMPTY)

# 2. Do cleanup passes alone work?
model = ct.convert(prog, convert_to="mlprogram", pass_pipeline=ct.PassPipeline.CLEANUP)

# 3. Does another backend work?
model = ct.convert(prog, convert_to="neuralnetwork", pass_pipeline=ct.PassPipeline.EMPTY)

# 4. Does precision change the failure?
model = ct.convert(prog, convert_to="mlprogram", compute_precision=ct.precision.FLOAT32)
```

## 3. Pass pipeline bisection workflow

When the default pipeline fails but an empty pipeline works:

```python
import coremltools as ct

base = ct.PassPipeline.DEFAULT
passes = list(base.passes)

# Try a prefix to find the first failing region.
probe = ct.PassPipeline.EMPTY
probe.passes = passes[: len(passes) // 2]
model = ct.convert(prog, convert_to="mlprogram", pass_pipeline=probe)
```

Refine the pass list until the failing pass is isolated. Then decide whether to remove it, set an option, or rewrite MIL to avoid the pattern.

Useful patterns:

```python
# Remove one or more passes.
pipeline = ct.PassPipeline.DEFAULT
pipeline.remove_passes({"common::fuse_conv_batchnorm"})
model = ct.convert(prog, pass_pipeline=pipeline)

# Avoid folding very large constants into a single const.
pipeline = ct.PassPipeline.DEFAULT
pipeline.set_options("common::const_elimination", {"skip_const_by_size": "1000000"})
model = ct.convert(prog, pass_pipeline=pipeline)
```

Do not set options for a pass that is absent from `pipeline.passes`; pipeline validation will reject that configuration.

## 4. Deployment compatibility workflow

Use explicit targets when the same MIL graph behaves differently across OS targets.

```python
for target in [ct.target.iOS15, ct.target.iOS16, ct.target.iOS17, ct.target.iOS18]:
    try:
        model = ct.convert(prog, convert_to="mlprogram", minimum_deployment_target=target)
        print("ok", target, model.get_spec().specificationVersion)
    except Exception as exc:
        print("fail", target, exc)
```

If a target-specific failure says the converted model uses later features, do one of the following:

- Raise `minimum_deployment_target` if deployment policy allows it.
- Replace newer MIL ops or patterns with older equivalents.
- Try the neural network backend if the model does not require ML Program-only features.
- For stateful models and newer ML Program features, verify the minimum deployment target and runtime OS support together.

## 5. Composite/custom operator workflow

Use this when source conversion fails with an unsupported op.

Decision order:

1. Prefer a source-framework translation that decomposes the op into existing MIL Builder ops.
2. Register a TensorFlow or PyTorch composite translation and rerun conversion.
3. Only if decomposition cannot represent the op, register a custom MIL op with `is_custom_op=True` and provide custom layer bindings.
4. Use `convert_to="neuralnetwork"` for custom layers. Do not expect custom layers to work in ML Programs.
5. Ensure the Swift/Core ML custom layer implementation matches the Python binding `class_name`, `input_order`, and `parameters`.

Composite PyTorch skeleton:

```python
from coremltools.converters.mil.frontend.torch.torch_op_registry import register_torch_op
from coremltools.converters.mil.frontend.torch.ops import _get_inputs
from coremltools.converters.mil import Builder as mb

@register_torch_op
def selu(context, node):
    x = _get_inputs(context, node, expected=1)[0]
    y = mb.elu(x=x, alpha=1.6732632423543772)
    y = mb.mul(x=y, y=1.0507009873554805, name=node.name)
    context.add(y)
```

Custom MIL op skeleton:

```python
from coremltools.converters.mil.mil import Operation, types
from coremltools.converters.mil.mil.input_type import InputSpec, TensorInputType
from coremltools.converters.mil.mil.ops.defs._op_reqs import register_op

@register_op(doc_str="Custom layer", is_custom_op=True)
class custom_passthrough(Operation):
    input_spec = InputSpec(x=TensorInputType(type_domain="T"))
    type_domains = {"T": (types.fp16, types.fp32)}
    bindings = {
        "class_name": "CustomPassthrough",
        "input_order": ["x"],
        "parameters": [],
        "description": "Custom passthrough layer",
    }

    def type_inference(self):
        return self.x.sym_type
```

## 6. Typed execution and numeric-debug workflow

Use ML Program typed execution to separate precision regressions from conversion correctness.

```python
fp32_model = ct.convert(prog, convert_to="mlprogram", compute_precision=ct.precision.FLOAT32)
fp16_model = ct.convert(prog, convert_to="mlprogram", compute_precision=ct.precision.FLOAT16)
```

If predictions are available, compare outputs:

```python
from coremltools.models.ml_program.experimental.debugging_utils import (
    MLModelComparator,
    compute_snr_and_psnr,
)

comparator = MLModelComparator(reference_model=fp32_model, target_model=fp16_model)

async def compare(inputs):
    return await comparator.find_failing_ops(
        inputs=inputs,
        compare_outputs=lambda op, ref, tgt: compute_snr_and_psnr(tgt, ref)[1] >= 40.0,
    )
```

If float16 is the issue:

- Convert the full ML Program with `ct.precision.FLOAT32` to confirm the hypothesis.
- Use selective `ct.transform.Float16ComputePrecision(...)` to preserve float32 for sensitive operations while allowing float16 elsewhere.
- For neural networks, use CPU-only prediction to force float32 execution, but treat that as a runtime choice rather than a typed model guarantee.

## 7. Experimental inspector/validator workflow

Use the experimental utilities after conversion succeeds and the problem is in intermediate outputs or runtime behavior.

```python
import coremltools as ct
from coremltools.models.ml_program.experimental.debugging_utils import (
    MLModelInspector,
    MLModelValidator,
)

inspector = MLModelInspector(model=mlmodel, compute_units=ct.ComputeUnit.CPU_ONLY)
print(inspector.output_names)

async def inspect_some(inputs):
    async for name, value in inspector.inspect(
        inputs=inputs,
        output_names=["add", "relu"],
        num_predict_intermediate_outputs=2,
    ):
        print(name, value.shape, value.dtype)

validator = MLModelValidator(model=mlmodel, compute_units=ct.ComputeUnit.CPU_ONLY)

async def find_nan(inputs):
    return await validator.find_failing_ops_with_nan_output(inputs=inputs)
```

Boundaries:

- `MLModelInspector` supports ML Programs only.
- The APIs are experimental and asynchronous.
- Output retrieval requires prediction/runtime support; on unsupported systems, conversion/save may work while inspector retrieval fails.
- Use `num_predict_intermediate_outputs` to control how many intermediate outputs are fetched per prediction call; smaller values can be slower but reduce per-call output pressure.

## 8. Submodel extraction workflow

When one intermediate output looks suspicious, extract a smaller Core ML model around it.

```python
from coremltools.converters.mil.debugging_utils import extract_submodel

submodel = extract_submodel(
    model=mlmodel,
    outputs=["suspect_output"],
    inputs=["x"],
)
submodel.save("suspect_submodel.mlpackage")
```

Notes:

- For neural networks, extraction works only on in-memory models returned directly by conversion.
- For ML Programs, extraction works for in-memory models and models loaded from disk when weights are available.
- The requested output names must be unique and present in the target function.

## 9. Smoke-script workflow

Use the bundled smoke script to avoid mixing repo-specific source-framework issues with coremltools MIL/backend availability.

```bash
python scripts/mil_smoke.py --help
python scripts/mil_smoke.py --convert-to neuralnetwork --output mil_smoke.mlmodel
python scripts/mil_smoke.py --convert-to mlprogram --compute-precision float32 --output mil_smoke.mlpackage
```

Interpretation:

- Builder failure means basic MIL construction/type inference is broken.
- Neural network success plus ML Program save failure points toward ML Program backend/native package support.
- Conversion success plus prediction failure points toward Core ML runtime availability, compute units, or input formatting.
