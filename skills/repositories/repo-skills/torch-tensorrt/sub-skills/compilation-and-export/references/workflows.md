# Compilation Workflows

## Route selection

| Route | Best for | Trade-offs |
| --- | --- | --- |
| `torch.compile(..., backend="torch_tensorrt")` | Fast adoption inside PyTorch 2.x code, no immediate artifact requirement. | First call compiles; graph breaks/recompilation can surprise users; save/deploy plan is less explicit. |
| `torch_tensorrt.compile(..., ir="dynamo")` | Explicit AOT compile of a module with representative inputs and options. | Requires CUDA/TensorRT-compatible environment; users must manage input specs and artifact choices. |
| `torch.export.export` + `torch_tensorrt.dynamo.compile` | Dynamic shapes, export-first projects, raw engine extraction, AOTInductor/ExecuTorch packaging. | More moving parts; `dynamic_shapes` mapping must align with `Input` ranges. |
| TorchScript frontend | Legacy `.ts`, DLA, and C++/libtorch workflows. | Requires TorchScript frontend/runtime feature gates; not the default recommendation for new Python workflows. |

## Workflow A: one-line PyTorch 2.x integration

```python
import torch
import torch_tensorrt

model = MyModel().eval().cuda()
compiled = torch.compile(
    model,
    backend="torch_tensorrt",  # some examples also use backend="tensorrt"
    options={
        "enabled_precisions": {torch.float16},
        "min_block_size": 3,
    },
)

x = torch.randn(8, 3, 224, 224, device="cuda")
with torch.inference_mode():
    y = compiled(x)  # compilation happens on the first observed graph
```

Use when the user does not need export artifacts and can tolerate first-call compile latency. If the model has data-dependent control flow, many shape variants, or repeated graph breaks, use the explicit export/AOT flow instead.

## Workflow B: AOT Dynamo compile from a module

```python
import torch
import torch_tensorrt

model = MyModel().eval().cuda()
example = torch.randn(4, 3, 224, 224, device="cuda")

compiled = torch_tensorrt.compile(
    model,
    ir="dynamo",
    inputs=[example],
    enabled_precisions={torch.float32},
    min_block_size=5,
)

torch.testing.assert_close(compiled(example), model(example), rtol=1e-4, atol=1e-4)
```

Prefer this when the user wants an explicit compile step. Replace tensor inputs with `torch_tensorrt.Input` specs for dynamic shapes or when preserving dtype/layout is important.

## Workflow C: dynamic-shape export-first compile

```python
import torch
import torch_tensorrt

class Encoder(torch.nn.Module):
    def forward(self, input_ids, attention_mask):
        return (input_ids.float() * attention_mask.float()).sum(dim=1)

model = Encoder().eval().cuda()
example = (
    torch.ones(4, 16, dtype=torch.int64, device="cuda"),
    torch.ones(4, 16, dtype=torch.int64, device="cuda"),
)
batch = torch.export.Dim("batch", min=1, max=8)
seq = torch.export.Dim("sequence", min=1, max=64)
exported = torch.export.export(
    model,
    example,
    dynamic_shapes={"input_ids": {0: batch, 1: seq}, "attention_mask": {0: batch, 1: seq}},
)

inputs = [
    torch_tensorrt.Input(min_shape=(1, 1), opt_shape=(4, 16), max_shape=(8, 64), dtype=torch.int64, name="input_ids", shared_dims={0: "batch", 1: "sequence"}),
    torch_tensorrt.Input(min_shape=(1, 1), opt_shape=(4, 16), max_shape=(8, 64), dtype=torch.int64, name="attention_mask", shared_dims={0: "batch", 1: "sequence"}),
]
compiled = torch_tensorrt.dynamo.compile(exported, inputs=inputs, min_block_size=1)
```

Make the PyTorch export dynamic dimension names and Torch-TensorRT `Input` ranges tell the same story. Do not use an `opt_shape` that is unrepresentative of production traffic.

## Workflow D: inspect coverage before committing

```python
compiled = torch_tensorrt.compile(
    model,
    ir="dynamo",
    inputs=inputs,
    dryrun=True,
    min_block_size=3,
    torch_executed_ops={torch.ops.aten.nonzero.default},
)
```

Use dryrun or compile analysis when the user asks, "Will this model be supported?" or when a full compile is expensive. If `require_full_compilation=True` fails, either allow fallback, rewrite the model, or route to custom converter/plugin guidance.

## Workflow E: choose a saved artifact

1. Use `.ep` / `output_format="exported_program"` for Python-side loading through `torch.export.load(...).module()` or `torch_tensorrt.load(...).module()`.
2. Use `.ts` / `output_format="torchscript"` only when runtime libraries and TorchScript support are present and C++/libtorch deployment is required.
3. Use `.pt2` / `output_format="aot_inductor"` for Linux AOTInductor packaging that runs without importing Torch-TensorRT at inference time.
4. Use `.engine` bytes from `convert_exported_program_to_serialized_trt_engine` when the entire model must be a raw TensorRT engine with no PyTorch wrapper.
5. Use `.pte` only for ExecuTorch workflows with the required extra packages and target runtime.

Read `serialization-and-engines.md` before writing a final save/load recipe.

## Numerical validation

Always include a correctness check unless the task is only static planning:

```python
with torch.inference_mode():
    eager = model(*example_inputs)
    actual = compiled(*example_inputs)
torch.testing.assert_close(actual, eager, rtol=1e-3, atol=1e-3)
```

Use looser tolerances for FP16/INT8/FP8, document why, and compare task-level metrics for models where elementwise closeness is not meaningful.
