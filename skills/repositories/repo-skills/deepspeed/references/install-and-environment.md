# Install and Environment

Read this before installing DeepSpeed, debugging imports, or deciding whether a command is safe to run. DeepSpeed can work as a Python package with JIT-built optional ops, but many high-performance paths need compatible PyTorch, accelerator drivers, CUDA/ROCm/vendor toolchains, and optional extras.

## Baseline Install Pattern

- Install PyTorch first. DeepSpeed setup and runtime inspect PyTorch and accelerator capabilities.
- Install the base package for general API/config inspection or standard usage: `pip install deepspeed`.
- Use optional extras only when the workflow needs them, such as autotuning, sparse attention/pruning, inference extras, stable diffusion examples, or deepcompile.
- Prefer JIT-built ops for normal installs unless the user explicitly wants prebuilt ops or a wheel build.
- Run `ds_report` after install to inspect accelerator and op compatibility before trying a training or inference job.

## Optional Dependency Tiers

| Tier | Use when | Safety |
| --- | --- | --- |
| Base package | Config, launcher help, Python API signatures, CPU-only planning. | Safe to inspect. |
| PyTorch CUDA/ROCm/vendor backend | Real GPU training, inference kernels, distributed collectives. | Verify driver, wheel, and toolkit compatibility first. |
| Prebuilt/JIT ops | Fused optimizers, inference kernels, sparse attention, AIO/GDS, quantizer ops. | May compile or fail on missing toolchains. |
| Autotuning/profiling/monitor extras | Running tuning jobs, model profiling, WandB/Comet/TensorBoard/CSV logging. | May launch workloads or require credentials/network. |
| NVMe/GDS tools | DeepNVMe, `ds_io`, `ds_nvme_tune`, AIO/GDS benchmarking. | Writes files and depends on storage/GDS stack. |

## Build and JIT Flags

- `DS_BUILD_OPS=1` requests prebuilding compatible ops during install or wheel build.
- `DS_BUILD_<OP_NAME>=1` requests a specific op when the op builder exposes that flag.
- `TORCH_EXTENSIONS_DIR` controls where JIT extension builds are cached.
- `TORCH_CUDA_ARCH_LIST` constrains CUDA architectures for builds, useful when building wheels for target GPU generations.
- `DS_SKIP_CUDA_CHECK=1` can bypass some version checks, but use it only when the user accepts the risk of building against a known-compatible but mismatched toolkit stack.

## Backend Notes

- CUDA workflows need a PyTorch CUDA wheel compatible with the driver and often a local CUDA toolkit when compiling ops.
- A CUDA-capable driver alone is not the same as a complete CUDA build environment; missing `CUDA_HOME` or `nvcc` can still block op compatibility probes or builds.
- CPU-only environments are useful for documentation, config, and API inspection, but they do not verify fused CUDA kernels, NCCL, FlashAttention, GDS, or performance-sensitive inference.
- Vendor accelerators such as XPU, HPU, NPU, MLU, SDAA, and others depend on DeepSpeed's accelerator abstraction plus vendor package/toolkit availability.

## Safe Validation Order

1. Run `python -c "import torch; print(torch.__version__, torch.cuda.is_available())"`.
2. Run `python -c "import deepspeed; print(deepspeed.__version__)"`.
3. Run `ds_report` or `python -m deepspeed.env_report`.
4. Run sub-skill-specific inspectors before native tests.
5. Only then run launcher jobs, distributed tests, op builds, benchmarks, or storage tools.
