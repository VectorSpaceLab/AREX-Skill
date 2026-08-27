---
name: compilation-and-export
description: "Use this sub-skill for Torch-TensorRT model compilation, dynamic
  input planning, torch.export workflows, save/load formats, raw TensorRT
  engines, and compile-time troubleshooting."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 3-Clause
---

# Torch-TensorRT Compilation and Export

Use this sub-skill when the user wants to turn a PyTorch model into a TensorRT-backed callable module or deployable artifact.

## First decision: compile route

| User situation | Recommended route |
| --- | --- |
| Wants a one-line experiment or easy integration with PyTorch 2.x | `torch.compile(model, backend="torch_tensorrt")` or `backend="tensorrt"` with options. |
| Wants ahead-of-time control, explicit inputs, and a Python-callable compiled module | `torch_tensorrt.compile(model, ir="dynamo", inputs=[...])`. |
| Already uses `torch.export`, needs dynamic shape control, or wants raw engine export | `torch.export.export(...)` then `torch_tensorrt.dynamo.compile(...)` or `convert_exported_program_to_serialized_trt_engine(...)`. |
| Needs legacy TorchScript or C++ `.ts` artifacts | Use only if `ENABLED_FEATURES.torchscript_frontend` and runtime libraries are present; otherwise route to deployment/build guidance. |
| Needs to understand coverage before compiling | Use `dryrun`, `require_full_compilation`, `torch_executed_ops`, and `min_block_size`; route debugging details to extensibility/debugging. |

Read `references/workflows.md` for full recipes and route selection.

## Minimum safe workflow

1. Verify install/features with the root environment probe if the environment is unknown.
2. Put the model in eval mode and move model plus representative inputs to CUDA.
3. Decide static or dynamic inputs. For dynamic shapes, create `torch_tensorrt.Input(min_shape=..., opt_shape=..., max_shape=..., dtype=...)` and align any `torch.export` dynamic dimensions.
4. Start with FP32 or FP16 only after checking numerical tolerance expectations. Avoid INT8/FP8/FP4 until ModelOpt or calibration prerequisites are explicit.
5. Compile a small representative shape, run the compiled output and PyTorch output, and compare with `torch.testing.assert_close` at task-appropriate tolerances.
6. Save only after execution works. Choose `.ep`, `.ts`, `.pt2`, `.engine`, or `.pte` from the artifact matrix.

## API/reference routing

- Read `references/api-reference.md` for public signatures and setting categories.
- Read `references/dynamic-shapes-and-inputs.md` for `Input`, `Device`, `torch.export` dynamic shapes, `shared_dims`, and multiple optimization profiles.
- Read `references/serialization-and-engines.md` before saving/loading, extracting raw engines, cross-compiling for Windows, or choosing deployment artifacts.
- Read `references/troubleshooting.md` for compile errors, graph breaks, unsupported ops, dynamic-shape errors, precision mismatches, and runtime library surprises.
- Run `scripts/compile_probe.py --help` to inspect the bundled tiny compile/dryrun helper. Run it with `--compile` only when a compatible CUDA/TensorRT environment is available.

## Common patterns

### JIT-style `torch.compile`

```python
import torch
import torch_tensorrt

model = MyModel().eval().cuda()
optimized = torch.compile(
    model,
    backend="torch_tensorrt",
    options={"enabled_precisions": {torch.float16}, "min_block_size": 3},
)
out = optimized(torch.randn(1, 3, 224, 224, device="cuda"))  # first call compiles
```

Use this when the user wants to keep PyTorch calling semantics and does not need a saved artifact immediately.

### Ahead-of-time Dynamo compile

```python
import torch
import torch_tensorrt

model = MyModel().eval().cuda()
inputs = [torch_tensorrt.Input((1, 3, 224, 224), dtype=torch.float32)]
compiled = torch_tensorrt.compile(model, ir="dynamo", inputs=inputs)
```

Use explicit `Input` objects for reusable code and dynamic shapes; use real tensors when the model is static and simple.

### Export first, compile second

```python
import torch
import torch_tensorrt

model = MyModel().eval().cuda()
example = (torch.randn(4, 128, device="cuda"),)
batch = torch.export.Dim("batch", min=1, max=16)
exported = torch.export.export(model, example, dynamic_shapes={"x": {0: batch}})
compiled = torch_tensorrt.dynamo.compile(
    exported,
    inputs=[torch_tensorrt.Input(min_shape=(1, 128), opt_shape=(4, 128), max_shape=(16, 128))],
)
```

Use this when export constraints, dynamic shape names, or artifact packaging matter.

## Guardrails

- Do not promise CPU fallback as a substitute for TensorRT verification. Torch-TensorRT compilation is a CUDA/TensorRT workflow.
- Do not treat source examples as runtime dependencies. Write task-local code or use bundled scripts.
- If the user needs unsupported-op triage, route to `../extensibility-and-debugging/SKILL.md` after collecting a dryrun/debugger result.
- If the user needs runtime speedups, route to `../runtime-optimization/SKILL.md` after compile correctness is established.
- If the user asks where to run the artifact, route to `../deployment-and-distributed/SKILL.md` before choosing save format.
