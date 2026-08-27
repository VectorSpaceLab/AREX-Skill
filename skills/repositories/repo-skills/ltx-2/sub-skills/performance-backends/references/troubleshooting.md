# Performance troubleshooting

Use this matrix when backend advice, compile flags, or accelerator assumptions fail.

## Symptom to recovery map

| Symptom | Likely cause | Recovery |
|---|---|---|
| CUDA import works but runtime generation still fails | Driver, wheel, or cuDNN mismatch; or a model-specific config issue. | Recheck the installed CUDA wheel stack first. If the repo documents a cuDNN override, treat it as the install path to follow rather than a runtime workaround. |
| `ltx-kernels` import fails | Optional compiled package not built or not installed. | Decide whether the user really needs an optional accelerator. If yes, build it on a CUDA host with the required toolkit; otherwise use the fallback backend. |
| `nvcc` missing | Source build requested without a CUDA toolkit. | Explain that this only matters for source builds. Use a prebuilt wheel or a non-kernel fallback if the goal is just inference. |
| `nvfp4` requested on A100 / Hopper / Ada | Blackwell-only path. | State that NVFP4 is unavailable on this hardware and recommend `fp8-cast`, `fp8-scaled-mm`, or offload instead. |
| `blackwell_dsl` requested on non-Blackwell hardware | Datacenter Blackwell-only DSL path. | Do not attempt a build. Recommend a non-DSL DiffVAE mode. |
| DiffVAE `combined_compile` raises because NATTEN is missing | Required backend missing. | Use `chunked_eager` or `chunked_compile` fallback, or install the required backend on a suitable machine. |
| DiffVAE decode hits illegal memory access | Usually backend / wheel mismatch, non-contiguous inputs, or an unsupported fallback path. | First verify the attention backend and wheel pins. Then fall back to a simpler backend. Do not assume the tiling config is the root cause. |
| `torch.compile` with `reduce-overhead` or capture fails | Weights not resident, unsupported backend combination, or bad compile config. | Use the safer eager mode first. If compile is still desired, reduce the scope and verify the config keys. |
| `torch.compile` cache reuse gives bad output or memory access | Unsafe dynamic-shape guard skipping or reusing a graph beyond its token envelope. | Stop using the unsafe cache flag and recompile for the larger shape. |
| OOM on a single GPU | Model too large for current VRAM, or too much resident memory. | Try `fp8-cast`, then `--offload cpu`, then `disk`. For DiffVAE, pick a lighter decode mode. |
| OOM during block streaming | Buffer slots or layout choice too large. | Reduce resident weights, choose the streaming path intentionally, or fall back to a simpler offload strategy. |
| Multi-GPU request on a single GPU host | Host does not satisfy the parallelism gate. | Tell the user MGPU needs multiple GPUs and Linux/NCCL. Suggest single-GPU performance options instead. |
| SP request without built `ltx-kernels` | Missing mandatory all2all kernel. | Say SP is unavailable until the compiled kernels exist. Fall back to single-GPU or another memory strategy. |
| TDP used as a memory workaround | Incorrect mental model. | Clarify that TDP is an upscale/latency technique, not a fit-a-bigger-model trick. |

## Safe recovery order

1. Confirm the exact backend path the user asked for.
2. Check whether the gate is hardware, wheel, or optional-package related.
3. Prefer a documented fallback path that keeps the job runnable.
4. Only mention a build/install step if the user really needs the optional accelerator.

## Notes on repo-specific overrides

- The repository documents a cuDNN override for host compatibility. If a wheel stack mismatch appears, prefer the repo's documented alignment path rather than ad hoc package mixing.
- Missing `nvcc` is only a problem for source builds of optional CUDA kernels.
- Optional accelerator checks should never be treated as a failure of the base CUDA runtime unless the user explicitly required that accelerator.
