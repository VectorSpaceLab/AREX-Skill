# Torch-TensorRT Kernel API

Torch-TensorRT exposes a QDP/custom-kernel layer under `torch_tensorrt.kernels`. Use it when the user wants to define a custom CUDA/PTX kernel with Torch-TensorRT integration rather than a standard TensorRT converter.

## Core symbols seen in this source snapshot

- `KernelSpec`
- `cuda_kernel_op`
- `ptx_op`
- input/output declaration helpers such as `InputDecl`, `OutputDecl`, `Custom`, `Elementwise`, `Reduction`, `ReduceDims`, `Numel`, `SameAs`, `ScalarInput`, and `DimSize`

## Public signatures captured from inspection

```python
torch_tensorrt.kernels.KernelSpec(kernel_source, kernel_name, inputs=None, outputs=None, extras=(), geometry=None, include_paths=None, compile_std='c++17', arch_override=None)

torch_tensorrt.kernels.cuda_kernel_op(
    op_name,
    spec,
    *,
    meta_fn=None,
    eager_fn=None,
    aot_fn=None,
    schema=None,
    supports_dynamic_shapes=True,
    requires_output_allocator=False,
    priority=ConverterPriority.STANDARD,
    capability_validator=None,
)

torch_tensorrt.kernels.ptx_op(
    op_name,
    ptx,
    kernel_name,
    meta_fn,
    eager_fn,
    aot_fn,
    *,
    supports_dynamic_shapes=False,
    requires_output_allocator=False,
    priority=ConverterPriority.STANDARD,
    capability_validator=None,
    schema=None,
)
```

## How to think about it

- `KernelSpec` describes the kernel source and its inputs/outputs.
- `cuda_kernel_op` registers a higher-level custom CUDA kernel.
- `ptx_op` registers a PTX-backed operation when you already have PTX bytes.

## Practical guidance

- Start from a reproducible unsupported-op or custom-fusion need.
- Verify the model still behaves correctly in eager PyTorch before adding a kernel.
- Keep the kernel API in a bundled skeleton or issue repro, not in the original repo checkout.
- If the task is actually a converter problem rather than a custom kernel, route back to custom converters first.

## Safety notes

- QDP/kernel support may be unavailable in TensorRT-RTX or in standard builds without the necessary dependencies.
- Do not promise dynamic-shape support unless the chosen kernel path and validation confirm it.
- Keep generated skeletons small and explicit about the exact op schema they target.
