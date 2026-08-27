# Transformer Engine troubleshooting

Use this reference for cross-cutting Transformer Engine failures. Start with the exact symptom, then choose the narrowest fix.

## Quick triage

| Symptom | Likely cause | First action |
| --- | --- | --- |
| Missing shared object or extension import failure | The selected framework extension was not built or installed. | Re-run the install/build route with the intended `NVTE_FRAMEWORK`. |
| Empty metapackage / incomplete install | The payload extras were not installed. | Install the real `core`, `pytorch`, `jax`, or combined extra. |
| Version mismatch across TE packages or framework extension modules | Stale or mixed packages on the import path. | Reinstall a matched set in one environment. |
| CUDA/cuBLAS/cuDNN handle aborts or `cublasLtGetVersion` failures | Mixed CUDA library order or incompatible runtime libraries. | Re-check loader order, package versions, and run the bundled runtime inspector. |
| FP8 recipe rejected on A100 | The hardware gate is correct; A100 is BF16/FP16-only for this skill's runtime validation scope. | Keep the path BF16/FP16 and surface the reason string. |
| PyTorch compile or graph-capture instability | `torch.compile` or fused paths are too aggressive for the current stack. | Set `NVTE_TORCH_COMPILE=0` before importing TE. |
| JAX OOM before the first step | XLA preallocated too much memory or another process is occupying the GPU. | Set `XLA_PYTHON_CLIENT_PREALLOCATE=false` before importing JAX and retry a smaller smoke. |

## Shared loader-order rules

Mixed PyTorch/JAX environments are normal for Transformer Engine, but they are also easy to misconfigure.

- Import `torch` before `transformer_engine.pytorch` in standalone PyTorch probes.
- Import `jax` before `transformer_engine.jax` in standalone JAX probes.
- If a mixed environment still fails, use the bundled runtime inspector rather than guessing which framework is broken.
- Keep the intended CUDA, cuDNN, and NCCL library directories first in `LD_LIBRARY_PATH` when the environment uses external toolkit libraries.

## Common CUDA and cuBLAS/cuDNN failures

### Missing shared objects

If the error mentions `cudnn`, `cudart`, `curand`, `nvrtc`, or `cublas` shared objects, verify the runtime libraries are visible to the process and that the active installation was built for the same CUDA major.

### cuBLASLt or cuDNN handle aborts

If a process aborts around cuBLASLt or cuDNN handle creation:

1. Start a fresh Python process.
2. Run the runtime inspector.
3. Re-run the smallest BF16 smoke.
4. Only then retry a larger `TransformerLayer` or attention path.

These failures are frequently environmental rather than model-code bugs.

## Framework-specific follow-up

- For PyTorch install/build or `torch.distributed.fsdp._fully_shard` issues, continue in [sub-skills/pytorch/references/troubleshooting.md](../sub-skills/pytorch/references/troubleshooting.md).
- For JAX import, XLA, fused attention, or quantization-collection issues, continue in [sub-skills/jax/references/troubleshooting.md](../sub-skills/jax/references/troubleshooting.md).
- For source-build prerequisites, `nvcc`, or submodule issues, continue in [sub-skills/install-build/references/troubleshooting.md](../sub-skills/install-build/references/troubleshooting.md).

## What not to do

- Do not claim FP8 success on A100-class hardware.
- Do not treat a successful top-level package import as proof that the framework extension is usable.
- Do not jump straight to full `TransformerLayer` or distributed examples when the tiny smoke has not passed.
- Do not tell future agents to open the original repo docs or tests as the runtime fix; use the bundled scripts and references in this skill tree instead.
