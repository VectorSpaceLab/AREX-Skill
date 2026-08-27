# Runtime Optimization Troubleshooting

## CUDA Graph failures

Common symptoms:

- Capture fails on the first iteration.
- Replay works for one shape but fails for another.
- Outputs are stale, corrupted, or allocated differently than expected.

Actions:

1. Verify the compiled module runs correctly without CUDA Graphs.
2. Use static shapes and stable input/output allocation for the first graph test.
3. Avoid data-dependent control flow or allocation during capture.
4. If using TensorRT-RTX, decide whether to use `cuda_graph_strategy="whole_graph_capture"` inside `RuntimeSettings` or an outer `enable_cudagraphs` context; do not stack both without verifying the installed version supports the combination.
5. Reproduce with a tiny static-shape input before applying to a large model.

## Output allocator or preallocated output problems

- These APIs are runtime-build dependent. Check `ENABLED_FEATURES.torch_tensorrt_runtime` and test a small module first.
- Shape-varying outputs can invalidate preallocation assumptions.
- If output values are wrong only under allocator/preallocation contexts, remove those contexts and file a minimal repro with input shapes, package versions, and the compiled artifact type.

## Cache issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Cache miss after upgrade | TensorRT/PyTorch/Torch-TensorRT version changed. | Rebuild cache. |
| Cache hit but wrong behavior | Incompatible graph/weights/settings reused. | Use per-model cache directories and include settings in cache key naming. |
| Permission error | Cache directory not writable by runtime user. | Put cache under an application-managed writable directory. |
| TensorRT-RTX cache error | Runtime cache applied after context creation or shape/strategy mismatch. | Apply `RuntimeSettings` before first execute, clear cache, test static shape. |

## Serialization runtime failures

If a saved artifact loads but fails when executed:

1. Confirm artifact type: `.ep`, `.ts`, `.pt2`, `.engine`, or `.pte`.
2. Confirm runtime package flavor and feature gates match the artifact type.
3. Disable optional CUDA Graph and runtime cache settings.
4. Run a tiny static-shape save/load smoke.
5. Rebuild in a standard TensorRT environment if the failure appears TensorRT-RTX-specific.

## OOM and busy GPU

- `CUDA-capable device(s) is/are busy or unavailable` usually means GPU allocation failed before Torch-TensorRT tuning. Check `nvidia-smi`, choose an idle device with `CUDA_VISIBLE_DEVICES`, and run a PyTorch allocation smoke.
- Engine build OOM may require smaller max shapes, FP16, fewer simultaneous compilations, or model partition changes.
- Runtime OOM after successful compile may require output preallocation changes, lower batch/sequence, weight streaming, or resource partitioning.

## When this is a compile/debug issue instead

Route away from this sub-skill when:

- The model does not compile at all.
- The error names unsupported operators, missing converters, or graph partitioning.
- The user wants to author custom converters, TensorRT plugins, or QDP kernels.
- The user is selecting `.ep`/`.ts`/`.pt2`/`.engine` for a deployment target rather than tuning an already chosen runtime.
