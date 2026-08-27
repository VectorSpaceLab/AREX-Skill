# Dynamic Shapes and Input Specs

Torch-TensorRT needs representative input information to build TensorRT optimization profiles. Shape mistakes are a common source of compile failure, runtime failure, or poor performance.

## Static vs dynamic inputs

Use a real tensor or a static `Input` when the shape is fixed:

```python
x = torch.randn(1, 3, 224, 224, device="cuda")
compiled = torch_tensorrt.compile(model, ir="dynamo", inputs=[x])

# Equivalent explicit form
compiled = torch_tensorrt.compile(
    model,
    ir="dynamo",
    inputs=[torch_tensorrt.Input((1, 3, 224, 224), dtype=torch.float32)],
)
```

Use dynamic ranges when batch, sequence length, image size, or other dimensions vary:

```python
input_spec = torch_tensorrt.Input(
    min_shape=(1, 3, 224, 224),
    opt_shape=(4, 3, 512, 512),
    max_shape=(8, 3, 1024, 1024),
    dtype=torch.float16,
    name="images",
)
```

## Choosing min/opt/max

- `min_shape`: smallest shape the compiled engine must accept. Do not set it lower than the model can actually handle.
- `opt_shape`: the shape TensorRT optimizes most aggressively. Set it near production median or latency-critical traffic.
- `max_shape`: largest shape the engine must accept. Oversized maximums can increase build time and memory.
- Keep dtype and layout representative. Compiling with FP16 inputs but running FP32 inputs can cause conversion or performance surprises.

## Multiple inputs and shared dimensions

When two inputs share dimensions, make that explicit in both PyTorch export and Torch-TensorRT input specs.

```python
batch = torch.export.Dim("batch", min=1, max=8)
seq = torch.export.Dim("sequence", min=1, max=64)
example = {
    "input_ids": torch.ones(4, 16, dtype=torch.int64, device="cuda"),
    "attention_mask": torch.ones(4, 16, dtype=torch.int64, device="cuda"),
}
exported = torch.export.export(
    model,
    (),
    kwargs=example,
    dynamic_shapes={
        "input_ids": {0: batch, 1: seq},
        "attention_mask": {0: batch, 1: seq},
    },
)
inputs = [
    torch_tensorrt.Input(min_shape=(1, 1), opt_shape=(4, 16), max_shape=(8, 64), dtype=torch.int64, name="input_ids", shared_dims={0: "batch", 1: "sequence"}),
    torch_tensorrt.Input(min_shape=(1, 1), opt_shape=(4, 16), max_shape=(8, 64), dtype=torch.int64, name="attention_mask", shared_dims={0: "batch", 1: "sequence"}),
]
```

If the model accepts positional arguments, pass `arg_inputs`; if it accepts keyword arguments, pass `kwarg_inputs` and use names consistently.

## Multiple optimization profiles

Some models have distinct modes, such as LLM prefill and decode. Use multiple profiles only when the package version supports the needed `Input` profile shape and the runtime can select profiles correctly.

Guideline:

- Profile 1: batch/sequence ranges for prefill, optimized near typical prompt length.
- Profile 2: smaller token-step shape for decode, optimized for per-token latency.
- Keep output and cache shapes compatible with every selected profile.
- Test each profile with representative inputs before measuring performance.

## `torch.export` dynamic shapes alignment

Torch-TensorRT can consume an `ExportedProgram`. The `torch.export` dynamic-shape constraints and the TensorRT `Input` min/opt/max ranges must be compatible.

Failure signs:

- Export fails before Torch-TensorRT sees the model: fix `torch.export` dynamic constraints or model data-dependent control flow.
- TensorRT compile fails with profile or shape errors: inspect `Input` ranges and dtypes.
- Runtime fails for a shape within the claimed range: check whether that dimension was truly dynamic in export and whether every input shares the same named dimension.

## Marking dynamic dimensions in `torch.compile`

For JIT-style `torch.compile`, dynamic shape behavior depends on PyTorch Dynamo graph capture and recompilation. If the model recompiles for each shape, consider `torch._dynamo.mark_dynamic` or switch to explicit export/AOT compile with dynamic `Input` ranges.

## Troubleshooting checklist

- Model and all input tensors/specs are on CUDA or explicitly represent CUDA execution.
- `min <= opt <= max` for every dynamic dimension.
- The `opt_shape` is representative, not just arbitrary.
- Dtypes match expected model input dtypes.
- Batch and sequence dimensions shared across inputs are named consistently.
- The exported program accepts the same positional/keyword structure used during compile.
- Unsupported shape ops or data-dependent control flow are identified with dryrun/debugger before adding custom converters.
