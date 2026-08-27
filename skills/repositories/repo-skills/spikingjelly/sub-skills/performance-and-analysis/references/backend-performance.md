# Backend Performance Reference

## Backend selection matrix

| Backend/surface | Use when | Key constraints |
| --- | --- | --- |
| `backend="torch"` | Correctness baseline, CPU support, first reproduction, or comparing other backends | Always start here when a model has state/shape issues |
| `backend="cupy"` | CUDA acceleration for standard SpikingJelly neuron kernels | Requires a CUDA-capable PyTorch install plus matching `cupy-cuda11x` or `cupy-cuda12x` |
| `backend="triton"` | Multi-step GPU neuron execution and Triton/FlexSN work | GPU-only and multi-step oriented; predefined Triton neuron kernels use `step_mode="m"` |
| `triton_kernel.flexsn` / `neuron.FlexSN` | Generate kernels from a single-step neuronal dynamics function | The core signature is `[*inputs, *states] -> [*outputs, *states]`; Triton/HOP paths are multi-step and hardware-specific |
| `cuda_kernel` low-level helpers | Experimental spike-linear, fused IF/LIF-linear, and auto-CUDA code-generation work | Advanced surface; do not assume automatic density-based dispatch or broad model support |

## Backend operating rules

- Keep a `torch` backend baseline before using CuPy or Triton for speed claims.
- For multi-step neurons, feed time-major tensors such as `[T, N, ...]` and use `step_mode="m"`.
- Move both the module and inputs to the same CUDA device before choosing `cupy` or `triton`.
- Reset stateful modules with `functional.reset_net(model)` between independent timing windows.
- Time both forward and backward when the user asks about training speed; a forward-only smoke is not a benchmark.
- Treat first-run Triton compilation time separately from steady-state timing.

## Predefined Triton notes

The source tutorials and tests cover predefined Triton paths for common neuron kernels such as `IFNode`, `LIFNode`, and `PLIFNode`. Triton execution is intended for GPU multi-step workloads. The experimental `ActivationAwareIFNode` path is inference-oriented and rejects unsupported training/autograd paths rather than silently falling back.

## CuPy / CUDA notes

The CuPy backend is a CUDA runtime dependency, not a CPU substitute. It must match the installed CUDA/PyTorch wheel family. `cuda_kernel.spike_linear` and related low-level helpers expose specialized experimental kernels; use them only when the task explicitly concerns those kernels and tensor layouts.

## Safe validation

From this sub-skill directory, run:

```bash
python scripts/backend_smoke.py --json
python scripts/backend_smoke.py --backends torch --json
```

A skipped CuPy or Triton check means the optional dependency or CUDA device was not available in the target environment. A passed smoke proves only import/device/basic-forward viability, not full benchmark performance.
