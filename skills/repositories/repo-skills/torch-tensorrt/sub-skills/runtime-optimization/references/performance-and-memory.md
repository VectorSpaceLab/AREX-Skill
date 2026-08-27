# Performance and Memory Guidance

## Benchmarking rules

- Measure eager PyTorch and compiled Torch-TensorRT with the same input tensors, dtype, shape, batch size, and model mode.
- Use `model.eval()` and `torch.inference_mode()` unless the user's task explicitly needs training behavior.
- Exclude engine build, lazy initialization, and first-call TensorRT-RTX JIT time from steady-state latency unless the user is measuring cold-start.
- Use CUDA events or synchronize around wall-clock timers.
- For dynamic shapes, benchmark minimum, optimum, maximum, and high-traffic shapes separately.
- Report p50/p95 or per-shape averages when user traffic is heterogeneous.

## Why compiled latency may be poor

| Cause | Symptom | Response |
| --- | --- | --- |
| Tiny model or tiny batch | TensorRT overhead dominates. | Compare larger representative shapes; do not force TensorRT if PyTorch is faster. |
| Bad `opt_shape` | Median traffic is slower than expected. | Rebuild with an `opt_shape` near production median or add profiles. |
| Too many PyTorch fallback segments | Many CPU/PyTorch transitions or little speedup. | Use dryrun/debugger; tune `min_block_size`; decide fallback vs converter. |
| First-call compile/JIT included | First measurement much slower than later calls. | Separate cold-start and warm steady-state. |
| Dynamic-shape recompilation/specialization | New shapes are slow or asynchronous. | Use TensorRT profiles and TensorRT-RTX specialization settings intentionally. |
| Precision not optimized | FP32 runs slower than expected. | Try FP16 where accuracy and hardware allow. |
| Memory pressure | OOM, allocator churn, or lower occupancy. | Reduce shape ranges, batch size, workspace, or use resource/weight controls. |

## Memory reduction levers

Start with the least surprising change:

1. Lower `max_shape` or split overly broad dynamic profiles.
2. Reduce batch size or sequence length.
3. Use FP16 if accuracy allows.
4. Increase fallback for memory-heavy unsupported segments only if it helps end-to-end.
5. Use `enable_weight_streaming` or weight streaming context for large-weight models.
6. Use `offload_module_to_cpu`, `enable_resource_partitioning`, `cpu_memory_budget`, or `dynamically_allocate_resources` when the installed version supports them.
7. Avoid compiling many model variants simultaneously on the same GPU.

## Cache strategy

| Cache | Helps with | Watch out for |
| --- | --- | --- |
| Timing cache | TensorRT tactic timing across builds. | Invalidated by TensorRT/hardware/precision changes. |
| Engine cache | Reusing built TRT engines. | Must match graph, weights/settings where required, and target hardware compatibility. |
| TensorRT-RTX runtime cache | Runtime JIT kernel reuse. | RTX-only; apply before first execution; cache may be shape/strategy sensitive. |

## Dynamic profile planning

For a broad workload:

- Prefer a small number of meaningful profiles rather than one huge max range.
- Put `opt_shape` at a measured production mode.
- For LLM-like prefill/decode, use distinct profile plans for long prompt prefill and per-token decode when supported.
- Validate each profile's boundaries with real inputs before benchmarking.

## Reporting performance results

A good response to a user should include:

- Hardware and package versions.
- Model name/shape/dtype, precision settings, input ranges/profiles.
- Whether timings include cold start, engine build, or runtime cache warmup.
- Eager baseline, compiled latency, and speedup with tolerance/accuracy result.
- Any fallback segments, unsupported ops, or runtime caches used.
- Reproducible command or script the user can rerun.
