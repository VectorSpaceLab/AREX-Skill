# MMCV Install And Build Reference

## Package Variants

| Need | Install | Ops state | Notes |
| --- | --- | --- | --- |
| Image, video, transforms, visualization, and non-op utilities only | `mmcv-lite` | No compiled `mmcv._ext`; `mmcv.ops` imports fail | Smallest package for lite workflows. |
| NMS, ROI ops, deform conv, sparse conv, 3D/point-cloud ops, attention kernels, or custom losses | `mmcv` | Compiled ops expected when wheel/build matches environment | Full package in MMCV 2.x. |
| Source checkout with ops disabled | `MMCV_WITH_OPS=0 pip install -e .` | Installs distribution `mmcv-lite`, imports as module `mmcv` | Useful for inspection or non-op development. |
| Source checkout with ops enabled | `MMCV_WITH_OPS=1 pip install -e . -v` | Builds `mmcv._ext` when PyTorch/compiler/backend are usable | Default in MMCV 2.x source builds. |

In MMCV 2.x, the package split changed: `mmcv` is the full package with ops, and `mmcv-lite` is the lite package without ops. Do not install both in the same environment. If a user is switching variants, ask them to uninstall the existing variant first, then install the desired one.

Runtime dependencies from `requirements/runtime.txt` are `addict`, `mmengine>=0.3.0`, `numpy`, `packaging`, `Pillow`, `pyyaml`, `yapf`, and `regex` on Windows. `setup.py` adds an OpenCV dependency when an existing compatible OpenCV is not importable; install `opencv-python-headless` first when running on servers or minimal containers without GUI support.

## Recommended Install Flow

1. Inspect Python and PyTorch first:

   ```bash
   python -c "import sys; print(sys.version)"
   python -c "import torch; print(torch.__version__); print(torch.version.cuda); print(torch.cuda.is_available())"
   ```

2. If compiled ops are needed, prefer MIM because it selects OpenMMLab wheels using the active PyTorch/CUDA combination:

   ```bash
   pip install -U openmim
   mim install mmcv
   ```

3. If MIM downloads a source archive instead of a wheel, the requested Python/PyTorch/CUDA/MMCV combination likely has no matching prebuilt wheel. Either choose a supported version combination, build from source, or install `mmcv-lite` if ops are not needed.

4. For a pinned version, keep the package variant explicit:

   ```bash
   mim install mmcv==2.2.0
   pip install mmcv-lite==2.2.0
   ```

## Pip Wheel Selection

For full `mmcv`, select the wheel index by CUDA and PyTorch version. The generic pattern is:

```bash
pip install mmcv==2.2.0 -f https://download.openmmlab.com/mmcv/dist/{cu-or-cpu}/{torch-version}/index.html
```

Examples of selector values are `cu118` or `cpu` for the CUDA selector and `torch2.1` for the PyTorch selector. Verify against the active environment; installing a wheel built for a different PyTorch or CUDA ABI is a common cause of undefined symbols and shared-library load failures.

## Source Build Basics

Before building full `mmcv`, verify that PyTorch imports and that the desired backend toolchain is available. Useful probes:

```bash
python -c "import torch; print(torch.__version__); print(torch.version.cuda); print(torch.cuda.is_available())"
gcc --version
nvcc --version
```

Common Linux build choices:

```bash
MMCV_WITH_OPS=1 pip install -e . -v
MMCV_WITH_OPS=0 pip install -e . -v
```

Common build environment variables:

| Variable | Use |
| --- | --- |
| `MMCV_WITH_OPS=1` | Build/install full `mmcv` with native extension sources. |
| `MMCV_WITH_OPS=0` | Skip extension build and install distribution `mmcv-lite`. |
| `FORCE_CUDA=1` | Build CUDA ops even when `torch.cuda.is_available()` is false in the build host. |
| `TORCH_CUDA_ARCH_LIST` | Set GPU architectures for CUDA compilation, especially for older or specific GPUs. |
| `CUDA_HOME` / `CUDA_PATH` | Point PyTorch extension build to the intended CUDA toolkit. |
| `MMCV_CUDA_ARGS` | Pass extra CUDA compiler flags. |
| `MAX_JOBS` | Limit parallel build workers if the host runs out of memory. |
| `FORCE_MLU=1`, `MMCV_MLU_OPS_PATH` | Build Cambricon MLU support and optionally point to an existing mlu-ops library. |
| `FORCE_MUSA=1` | Build MUSA support when using the matching Torch-MUSA stack. |
| `FORCE_NPU=1` | Build Ascend NPU support when `torch_npu` is installed. |
| `FORCE_MPS=1` | Force MPS-flavored build path when supported by the PyTorch/macOS stack. |
| `MMCV_WITH_DIOPI=1` | Build DIOPI/DIPU support; requires the corresponding DIPU/DIOPI paths. |

Windows builds need a matching Visual Studio C++ compiler, CUDA toolkit when building GPU ops, and a PyTorch build compatible with that toolchain. CPU-only Windows full builds compile only CPU ops; CUDA Windows builds need `CUDA_HOME`/`CUDA_PATH` and often `TORCH_CUDA_ARCH_LIST`.

## Compatibility Checks

- Match the Python ABI, PyTorch version, CUDA version, and MMCV version when choosing wheels.
- A GPU being present is not enough: full ops require that the installed wheel or source build was compiled for a compatible backend.
- `torch.version.cuda` reports the CUDA runtime used by PyTorch; it can differ from the driver and local toolkit.
- Old GPUs may require explicit `TORCH_CUDA_ARCH_LIST`; otherwise runtime can fail with `invalid device function` or `no kernel image is available for execution`.
- `mmcv.utils.collect_env()` reports Python, CUDA, PyTorch, OpenCV, MMEngine, MMCV, compiler, and compiled CUDA facts. In lite installs, MMCV compiler fields are `n/a` because `mmcv.ops` is absent.

## Verification Commands

Use the bundled checker from this skill after any install:

```bash
python scripts/check_mmcv_install.py
python scripts/check_mmcv_install.py --require-ops
```

For a full CUDA build, require both ops import and CUDA availability:

```bash
python scripts/check_mmcv_install.py --require-ops --require-cuda
```

Manual quick checks:

```bash
python -c "import mmcv; print(mmcv.__version__)"
python -c "import mmcv, mmcv.ops; print(mmcv.__version__)"
python -c "from mmcv.utils import collect_env; print(collect_env())"
```

When `mmcv.ops` imports successfully, a tiny CPU `box_iou_rotated` call is a useful smoke test. Do not expect that check to work in `mmcv-lite`; missing `mmcv._ext` is expected there.
