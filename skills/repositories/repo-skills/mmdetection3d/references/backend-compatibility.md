# Backend Compatibility

## When to read

Read this before choosing CPU, CUDA, sparse-convolution, or optional project-extension paths for MMDetection3D tasks.

## Core runtime facts

- MMDetection3D v1.4.0 is built on PyTorch, MMEngine, MMCV 2.x, and MMDetection 3.x.
- The public docs state Python 3.7+, PyTorch 1.8+, CUDA 10.0+, and recommend installing MMEngine/MMCV/MMDetection with MIM.
- Many point-cloud models rely on CUDA-backed 3D operators or sparse-convolution backends. CPU-only execution is documented as experimental and mostly useful for limited monocular/SMOKE debugging or static checks.
- CPU is adequate for import checks, config parsing, command construction, dataset layout inspection, some 3D structures operations, and many documentation/planning tasks.

## Backend decision table

| Task | Minimum practical backend | CPU substitute | Notes |
| --- | --- | --- | --- |
| Import/package inspection | CPU | full | Verify `mmdet3d`, `mmcv`, `mmengine`, `mmdet`, and key APIs. |
| Config/model-zoo inspection | CPU | full | Use the config checker when MMEngine is installed. |
| Dataset layout and command planning | CPU | full | Do not run full conversion without user approval. |
| Lidar detection/segmentation model inference | CUDA for most configs | none for faithful model execution | Config/checkpoint and optional sparse backend must match. |
| Monocular 3D inference/debug | CUDA preferred | partial | CPU can be useful for narrow debugging but may be slow or unsupported by some ops. |
| Training point-cloud models | CUDA | none or partial only for limited debug | CPU training is experimental and not recommended. |
| KITTI rotate-IoU CUDA metric paths | CUDA + numba CUDA | none for that path | Some metric code paths use CUDA kernels. |
| Sparse-convolution model families | CUDA + selected sparse backend | none for backend-specific models | `spconv`, MinkowskiEngine, and TorchSparse are not interchangeable. |
| TorchServe packaging preflight | CPU | full for artifact checks | Live serving may use GPU depending handler/model. |

## Optional sparse backends

Install optional sparse backends only when the selected config/model family requires them:

- `spconv` / `spconv2.0`: used by voxel/sparse-convolution model families when installed. Wheels are CUDA-version-specific such as `spconv-cuXXX` and `cumm-cuXXX`.
- MinkowskiEngine: used by Minkowski sparse convolution configs such as some MinkUNet/MinkResNet variants. It can require compiler/OpenBLAS/CUDA compatibility.
- TorchSparse: used by TorchSparse-backed segmentation configs. It can require sparsehash and CUDA-compatible builds.

Do not install all sparse backends by default. If a model config names a backend-specific variant, install that variant and verify it independently.

## Safe verification ladder

1. Import and version check: `mmdet3d`, `torch`, `mmcv`, `mmengine`, `mmdet`.
2. CUDA probe when GPU execution is requested: `torch.cuda.is_available()` and a tiny tensor allocation.
3. Optional backend import: `spconv`, `MinkowskiEngine`, or `torchsparse` only when the selected model needs it.
4. Config parse check: use the configuration sub-skill checker.
5. Command construction: use the appropriate bundled command builder.
6. Only after the above, run model inference/training/evaluation if the user explicitly accepts checkpoint/data/runtime costs.

## Red flags

- `ImportError` for `mmcv.ops`: likely mismatched PyTorch/CUDA/MMCV wheel.
- `ModuleNotFoundError: spconv` or `MinkowskiEngine`: optional sparse backend missing for selected config.
- CUDA visible in `nvidia-smi` but `torch.cuda.is_available()` is false: wrong PyTorch build or incompatible driver/runtime.
- CPU-only environment used for a point-cloud model that requires 3D CUDA ops: treat as unverified, not as a successful backend substitution.
