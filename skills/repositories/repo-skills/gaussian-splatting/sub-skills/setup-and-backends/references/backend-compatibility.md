# Backend Compatibility

## When To Read

Read this when CUDA availability, GPU model, driver version, PyTorch wheel tag, compiler version, or custom extension build compatibility is part of the task.

## Required Backend Facts

For core Python workflows, gather these facts before choosing packages:

```bash
nvidia-smi
nvidia-smi --query-gpu=name,memory.total,driver_version,compute_cap --format=csv,noheader,nounits
python - <<'PY'
import torch
print(torch.__version__, torch.version.cuda, torch.cuda.is_available())
if torch.cuda.is_available():
    print(torch.cuda.get_device_name(0), torch.cuda.get_device_capability(0))
PY
```

Also check the compiler that `nvcc` will use:

```bash
nvcc --version
g++ --version
```

## Compatibility Rules

- The README requires a CUDA-ready GPU with compute capability 7.0+ for the optimizer and recommends 24 GB VRAM for paper-quality training.
- PyTorch CUDA runtime, `nvcc`, and the custom extension build must be compatible. The driver can support a maximum CUDA runtime, but the installed toolkit/compiler still matters for source builds.
- CUDA 11-era docs used Visual Studio 2019 on Windows and CUDA SDK 11.8; on Linux, use a GCC version supported by the chosen CUDA toolkit.
- Extension packages compiled against one PyTorch/CUDA ABI may fail with another. Rebuild `diff_gaussian_rasterization`, `simple_knn`, and `fused_ssim` after changing PyTorch.
- `fused_ssim` is optional for functionality: training falls back to the Python SSIM implementation if the import fails. `diff_gaussian_rasterization` and `simple_knn` are core.
- Sparse Adam requires the accelerated rasterizer branch described in the README. If `--optimizer_type sparse_adam` is used without that support, `train.py` exits with a sparse-adam install error.

## CPU Substitute Policy

| Workflow | CUDA needed? | CPU substitute |
|---|---:|---|
| CLI help, command building, data-layout validation | no | full |
| COLMAP conversion with `--no_gpu` | no CUDA inside this repo, but external COLMAP still needed | partial |
| `train.py` optimizer loop | yes | none |
| `render.py` offline rendering | yes | none |
| `metrics.py` as implemented | yes (`torch.cuda.set_device` and tensors on CUDA) | none |
| SIBR real-time viewer | OpenGL plus CUDA for realtime rasterization | partial documentation only |

Never report training/rendering as backend-verified from CPU-only checks.

## Accelerated Rasterizer and Sparse Adam

The README describes a training speed acceleration path:

1. Uninstall the default rasterizer package.
2. Switch the rasterizer submodule to the `3dgs_accel` branch.
3. Reinstall that submodule.
4. Add `--optimizer_type sparse_adam` when training.

This is a dependency-variant change. Record which rasterizer branch was installed and rerun backend checks after switching. If the accelerated branch is unavailable or not installed, keep `--optimizer_type default`.

## Common Compatibility Decisions

- If the driver supports a newer CUDA runtime but the repo's extension code fails with the host compiler, prefer a supported compiler for that CUDA version before forcing unsupported compiler flags.
- If `nvcc` is absent but PyTorch CUDA imports, source extension builds still fail. Install a matching toolkit/compiler or use a prebuilt environment that already contains the extensions.
- If an A100/Ampere or newer GPU is used, set an appropriate `TORCH_CUDA_ARCH_LIST` during extension builds to avoid unnecessary architectures and speed compilation.
- If the user only needs scene validation or command construction, use CPU-safe helper scripts and clearly state that the actual train/render backend remains unverified.
