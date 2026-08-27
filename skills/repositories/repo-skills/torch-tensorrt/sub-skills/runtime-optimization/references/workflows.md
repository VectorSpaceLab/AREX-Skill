# Runtime Optimization Workflows

## Workflow A: benchmark before tuning

Use representative inputs and include warmup:

```python
import torch

def time_module(module, inputs, warmup=10, iters=50):
    module(*inputs)
    torch.cuda.synchronize()
    for _ in range(warmup):
        module(*inputs)
    torch.cuda.synchronize()
    start = torch.cuda.Event(enable_timing=True)
    end = torch.cuda.Event(enable_timing=True)
    start.record()
    for _ in range(iters):
        module(*inputs)
    end.record()
    torch.cuda.synchronize()
    return start.elapsed_time(end) / iters
```

Compare eager, compiled first-call, and warmed compiled latency separately. For dynamic shapes, benchmark every important shape or profile.

## Workflow B: CUDA Graphs

```python
from torch_tensorrt import runtime

with runtime.enable_cudagraphs(compiled_module) as graph_module:
    for _ in range(5):
        _ = graph_module(*static_inputs)
```

Use when shapes and allocation patterns are stable. Avoid if the model receives many shapes or data-dependent allocations unless the runtime supports the selected strategy.

## Workflow C: preallocated outputs and output allocator

```python
from torch_tensorrt import runtime

with runtime.enable_output_allocator(compiled_module) as mod:
    y = mod(*inputs)

with runtime.enable_pre_allocated_outputs(compiled_module) as mod:
    y = mod(*inputs)
```

These reduce allocation overhead in supported runtime builds. Verify output shape stability and correctness under the exact workload.

## Workflow D: TensorRT-RTX runtime settings

TensorRT-RTX adds runtime JIT behavior. Configure runtime settings before the first execution context is created:

```python
from torch_tensorrt.runtime import RuntimeSettings

compiled.runtime_settings = RuntimeSettings(
    runtime_cache="./trt_rtx_runtime_cache.bin",
    dynamic_shapes_kernel_specialization_strategy="eager",  # lazy | eager | none
    cuda_graph_strategy="whole_graph_capture",              # disabled | whole_graph_capture
)
```

Use `lazy` when first-use latency must stay low and background specialization is acceptable. Use `eager` when the current shape's optimized kernel should be ready before returning. Use `none` to avoid specialization.

## Workflow E: scoped runtime config

```python
from torch_tensorrt import runtime

with runtime.runtime_config(compiled_module, dynamic_shapes_kernel_specialization_strategy="lazy"):
    out = compiled_module(*inputs)
```

Use for temporary overrides or when multiple modules share a controlled runtime setting. Do not assume a context manager changes an execution context that was already created with incompatible settings; verify behavior in the installed version.

## Workflow F: engine and timing caches

Compile with cache settings when repeated engine builds are costly:

```python
compiled = torch_tensorrt.dynamo.compile(
    exported,
    inputs=input_specs,
    timing_cache_path="./timing_cache.bin",
    cache_built_engines=True,
    reuse_cached_engines=True,
    engine_cache_dir="./engine_cache",
    engine_cache_size=5 * 1024**3,
)
```

Use a cache directory per model/settings/hardware compatibility group. Clear the cache when weights, graph, precision, TensorRT version, or hardware compatibility flags change.

## Workflow G: mutable module and refit

```python
import torch_tensorrt

mutable = torch_tensorrt.MutableTorchTensorRTModule(
    pytorch_model,
    immutable_weights=False,
    strict=True,
)
out = mutable(*inputs)
```

Use when weights change over time, such as adapter/refit workflows. If the user only changes input shapes, prefer dynamic shape profiles and runtime profile handling rather than refitting weights.

## Workflow H: memory pressure triage

1. Reduce max dynamic shapes and batch size.
2. Use FP16 if accuracy allows and hardware supports it.
3. Avoid compiling too many small subgraphs; tune `min_block_size` and fallback decisions.
4. Use timing/engine caches after correctness is proven.
5. Consider `enable_weight_streaming`, `offload_module_to_cpu`, `enable_resource_partitioning`, and `cpu_memory_budget` for large models.
6. Benchmark after each change; memory-saving can increase latency.
