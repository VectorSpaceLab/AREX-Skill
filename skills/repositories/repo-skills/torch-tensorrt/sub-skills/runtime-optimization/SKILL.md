---
name: runtime-optimization
description: "Use this sub-skill for Torch-TensorRT runtime performance
  controls, CUDA Graphs, output allocation, caches, TensorRT-RTX runtime
  settings, mutable modules, refit, weight streaming, and benchmark triage."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 3-Clause
---

# Torch-TensorRT Runtime Optimization

Use this sub-skill after a model compiles, or when a user asks about runtime latency, memory, caches, CUDA Graphs, output buffers, TensorRT-RTX settings, mutable modules, refit, or benchmark methodology.

## Start with correctness and observability

1. Confirm the compiled module produces correct outputs for representative inputs.
2. Verify `torch_tensorrt.ENABLED_FEATURES`; runtime APIs are gated by standard TensorRT vs TensorRT-RTX and by whether C++ runtime libraries are present.
3. Benchmark with warmups and CUDA synchronization/events. Do not time only the first call, because it may include engine build, lazy initialization, or TensorRT-RTX JIT work.
4. Use `references/performance-and-memory.md` for memory/latency triage before changing many knobs at once.

## Route by runtime need

| User goal | Read/run |
| --- | --- |
| Apply CUDA Graphs, output allocator, preallocated outputs, weight streaming, runtime config, or TensorRT-RTX settings | `references/workflows.md` |
| Need exact runtime API names and signatures | `references/api-reference.md` |
| Diagnose high latency, OOM, compile/runtime cache behavior, dynamic shape profile choice, or benchmark design | `references/performance-and-memory.md` |
| Debug runtime errors, cache/load failures, CUDAGraph invalidation, allocator issues, or RTX-only setting surprises | `references/troubleshooting.md` |
| Need a safe script to inspect runtime feature availability | `scripts/runtime_feature_probe.py --help` |
| Need a benchmarking template | `scripts/benchmark_latency_template.py --help` |

## Main workflows

### CUDA Graphs

Use CUDA Graphs only after shapes and memory addresses are stable enough for capture.

```python
from torch_tensorrt import runtime

with runtime.enable_cudagraphs(compiled) as graph_module:
    for _ in range(10):
        _ = graph_module(*example_inputs)
```

For TensorRT-RTX, CUDA graph strategy may also be set through `RuntimeSettings` or `runtime_config`.

### TensorRT-RTX runtime settings

```python
from torch_tensorrt.runtime import RuntimeSettings

compiled.runtime_settings = RuntimeSettings(
    runtime_cache="trt_rtx_cache.bin",
    dynamic_shapes_kernel_specialization_strategy="eager",
    cuda_graph_strategy="whole_graph_capture",
)
```

These fields are no-ops or unavailable outside TensorRT-RTX. Apply settings before first execution when the execution context is lazily created.

### Engine and timing caches

Use compile-time `timing_cache_path`, `cache_built_engines`, `reuse_cached_engines`, `engine_cache_dir`, and `engine_cache_size` when repeated builds or dynamic variants dominate latency. Cache paths should be writable, stable for the workload, and isolated per incompatible model/settings pair.

### Mutable modules and refit

Use `MutableTorchTensorRTModule` or `refit_module_weights` when weights change and recompiling every time would be expensive. Compile with `immutable_weights=False` when refit/mutability is required.

### Weight streaming and resource controls

Use weight streaming, `offload_module_to_cpu`, resource partitioning, or smaller max dynamic shapes for memory pressure. Validate latency after each change; some memory-saving settings trade off performance.

## Guardrails

- Runtime settings do not fix unsupported operators; route unsupported-op work to `../extensibility-and-debugging/SKILL.md`.
- Cache hits are only valid for compatible engine settings, target device properties, TensorRT versions, and model weights where applicable.
- CUDA Graph capture can fail when input shapes, allocation patterns, data-dependent behavior, or unsupported operations change between captures.
- Do not promise TensorRT-RTX cache/strategy behavior in a standard TensorRT build.
- Do not promise C++ runtime or TorchScript behavior from a Python-only wheel.
