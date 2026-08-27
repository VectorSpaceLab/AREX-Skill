# Setup and Backend Troubleshooting

## `ModuleNotFoundError: diff_gaussian_rasterization` or `simple_knn`

Likely causes:

- The repository was cloned without submodules.
- The extension packages were not installed into the active environment.
- The environment changed after extension installation.

Recovery:

1. Initialize submodules recursively.
2. Reinstall the extension packages after PyTorch is installed.
3. Run `scripts/check_backend.py --require-cuda --require-extensions`.

Do not continue to training until the extension imports pass.

## Missing `third_party/glm` During Rasterizer Build

The rasterizer build includes GLM headers from its nested submodule. If the compiler reports missing GLM headers, initialize nested submodules recursively or fetch the nested dependency through an approved mirror. A shallow top-level clone alone may not be enough.

## `unsupported GNU version` From `nvcc`

CUDA supports only certain host compiler versions. Use a compiler supported by the selected CUDA toolkit. For CUDA 12.1, GCC newer than the supported range can fail. Prefer installing or selecting a supported compiler over adding `-allow-unsupported-compiler` unless the user accepts the risk.

## `cuda/std/type_traits` or CCCL Header Missing

This usually means the CUDA toolkit headers are incomplete or mismatched. Install the matching CUDA CCCL/runtime development headers for the toolkit used by `nvcc`, then rebuild the extension.

## `torch.cuda.is_available()` Is False

Check:

- The PyTorch wheel is a CUDA build, not CPU-only.
- NVIDIA driver and container GPU passthrough are visible.
- The driver supports the CUDA runtime required by the PyTorch wheel.
- The task is not running on a CPU-only host.

If no compatible GPU is available, narrow the task to CPU-safe support workflows or report a required-backend block. Do not present CPU checks as a working training/rendering environment.

## `no kernel image is available`

The compiled extension or installed wheel does not include code for the GPU compute capability. Rebuild with the right `TORCH_CUDA_ARCH_LIST` or choose a compatible wheel/runtime.

## Sparse Adam Error

Symptom: `Trying to use sparse adam but it is not installed`.

Cause: `--optimizer_type sparse_adam` needs the accelerated rasterizer variant that exposes `SparseGaussianAdam`.

Recovery:

- Use `--optimizer_type default`, or
- Install the accelerated rasterizer branch described in the README and rerun backend checks.

## Viewer Tool Confusion

SIBR viewers are C++/OpenGL applications. A successful Python environment does not prove viewer binaries exist. Route viewer build/run issues to [../../viewers/SKILL.md](../../viewers/SKILL.md).

## COLMAP/ImageMagick Missing

`colmap` and `magick` are needed only for raw-image conversion. A prepared COLMAP or Blender dataset can be trained without them. Route conversion questions to [../../data-preparation/SKILL.md](../../data-preparation/SKILL.md).
