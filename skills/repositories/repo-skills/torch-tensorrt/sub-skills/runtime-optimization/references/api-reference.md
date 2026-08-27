# Runtime API Reference

Check `torch_tensorrt.ENABLED_FEATURES` before assuming these APIs are usable in the current environment.

## Context managers

```python
torch_tensorrt.runtime.enable_cudagraphs(compiled_module, *, cuda_graph_strategy=None)
torch_tensorrt.runtime.enable_output_allocator(module)
torch_tensorrt.runtime.enable_pre_allocated_outputs(module)
torch_tensorrt.runtime.weight_streaming(module)
torch_tensorrt.runtime.runtime_config(target_or_targets, **overrides)
```

- `enable_cudagraphs`: wraps a compiled module for CUDA Graph capture/replay. Use with stable shapes and memory behavior.
- `enable_output_allocator`: enables output allocator support for compatible compiled graph modules.
- `enable_pre_allocated_outputs`: uses preallocated output buffers to reduce runtime allocation overhead.
- `weight_streaming`: activates weight streaming behavior for supported modules.
- `runtime_config`: applies scoped runtime overrides to one or more target modules.

## TensorRT-RTX settings

```python
from torch_tensorrt.runtime import RuntimeSettings

RuntimeSettings(
    dynamic_shapes_kernel_specialization_strategy="lazy",
    cuda_graph_strategy="disabled",
    runtime_cache=...,  # path string or RuntimeCache object when supported
)
```

Values documented by the project:

- `dynamic_shapes_kernel_specialization_strategy`: `"lazy"`, `"eager"`, or `"none"`.
- `cuda_graph_strategy`: `"disabled"` or `"whole_graph_capture"`.
- `runtime_cache`: persistent cache path or cache object for TensorRT-RTX JIT artifacts.

These settings are TensorRT-RTX-specific. In standard TensorRT builds they may be no-ops or unavailable.

## Compile settings that affect runtime

| Setting | Runtime effect |
| --- | --- |
| `timing_cache_path` | Reuses TensorRT timing information across builds. |
| `cache_built_engines` / `reuse_cached_engines` | Stores/reuses built engines. |
| `engine_cache_dir` / `engine_cache_size` | Chooses where/how much engine cache storage to use. |
| `lazy_engine_init` | Defers engine initialization; may affect first execution latency and is disabled for some cross-compile modes. |
| `use_python_runtime` | Uses Python runtime path; can be necessary in Python-only environments and has implications for serialization. |
| `enable_weight_streaming` | Enables TensorRT weight streaming for large-weight models. |
| `immutable_weights=False` | Allows refit/mutable weights instead of assuming fixed weights. |
| `offload_module_to_cpu`, `enable_resource_partitioning`, `cpu_memory_budget`, `dynamically_allocate_resources` | Memory/resource controls for large models and constrained GPUs. |

## Mutable module

```python
torch_tensorrt.MutableTorchTensorRTModule(
    pytorch_model,
    device=None,
    immutable_weights=False,
    strict=True,
    prefer_deferred_runtime_asserts_over_guards=False,
    weight_streaming_budget=None,
    **kwargs,
)
```

Use when model weights or configuration mutate and the module should manage recompilation/refit decisions. Pass compile options through `**kwargs` as needed, but verify current-version behavior.

## Refit

`torch_tensorrt.dynamo.refit_module_weights(...)` is exposed in the Dynamo module. The exact callable behavior may vary by version. The practical rule is: compile with refit-compatible settings, keep engine/module association intact, and validate outputs after changing weights.

## Runtime cache hygiene

- Use writable relative or application-managed paths.
- Do not share one cache across incompatible models, TensorRT versions, precision settings, or hardware-compatibility flags unless the package explicitly supports it.
- Treat cache misses as expected after upgrades or graph changes.
- Do not use a cache hit as correctness proof; still compare outputs.
