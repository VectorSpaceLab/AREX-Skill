# Environment Guide

## When To Read

Read this when a user needs a gaussian-splatting environment, custom CUDA extension installation, optional conversion tools, or viewer build prerequisites.

## Repository Components

The codebase has four user-facing components:

1. Python optimizer (`train.py`) for training 3D Gaussians from SfM or Blender data.
2. Python offline renderer/metrics (`render.py`, `metrics.py`, `full_eval.py`).
3. Network viewer integration between `train.py` and a SIBR remote viewer.
4. SIBR real-time viewer for trained models.

The Python optimizer/renderer are CUDA workflows. The repo's historical environment file names these core dependencies:

- Python 3.7.13
- PyTorch 1.12.1, torchvision 0.13.1, torchaudio 0.12.1
- CUDA toolkit/runtime 11.6
- `plyfile`, `tqdm`, `opencv-python`, `joblib`
- pip installs from `submodules/diff-gaussian-rasterization`, `submodules/simple-knn`, and `submodules/fused-ssim`

The README also states that newer environments such as Python 3.8/PyTorch 2.0/CUDA 12 can work. Treat version choice as an engineering compatibility decision, not a promise that every version works.

## Minimal Python Workflow Setup

Use an isolated environment. Install PyTorch with a CUDA runtime first, then build the extensions against that PyTorch:

```bash
# Example shape; choose versions for the host driver/GPU and repo requirements.
conda create --yes --name gaussian_splatting python=3.10 pip
conda activate gaussian_splatting
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
python -m pip install plyfile tqdm opencv-python joblib
python -m pip install ./submodules/diff-gaussian-rasterization --no-build-isolation
python -m pip install ./submodules/simple-knn ./submodules/fused-ssim --no-build-isolation
```

If using Conda instead of pip wheels for PyTorch, still install/build the custom extensions after PyTorch is importable and `torch.version.cuda` matches the intended toolkit.

## Submodule Checklist

Python workflows need these submodules initialized:

- `submodules/diff-gaussian-rasterization`
- `submodules/simple-knn`
- `submodules/fused-ssim`
- the nested GLM dependency under the rasterizer submodule

A non-recursive clone commonly fails with `ModuleNotFoundError: diff_gaussian_rasterization`, missing `third_party/glm`, or CUDA compile errors. Initialize submodules before building:

```bash
git submodule update --init --recursive
```

If network policies block one submodule, fetch that dependency through the user's approved mirror/proxy. Do not replace a missing extension with a CPU-only claim; it only postpones the required backend failure.

## External Tools

These are not Python package imports, but they affect selected workflows:

| Tool | Needed for | Required for core Python training? |
|---|---|---|
| CUDA-capable NVIDIA GPU | training, rendering, metrics, real-time viewer | yes for Python train/render/metrics |
| CUDA compiler/toolkit and compatible C++ compiler | building custom extensions | yes when wheels are not already built |
| COLMAP | converting raw images into SfM layout | no if data is already prepared |
| ImageMagick `magick` | optional resized image folders in conversion | no unless `--resize` conversion is selected |
| CMake + system OpenGL/SIBR dependencies | building SIBR viewers | no for Python train/render |

## Installation Verification

After installation, use a safe preflight before running expensive workflows:

```bash
python scripts/check_backend.py --repo-root /path/to/checkout --require-cuda --require-extensions --tools
```

A good Python workflow environment proves all of the following:

- `torch` imports and `torch.cuda.is_available()` is true.
- A tiny CUDA tensor can be allocated.
- `diff_gaussian_rasterization`, `simple_knn._C`, and `fused_ssim` import.
- Repo modules such as `arguments`, `scene`, and `gaussian_renderer` import from the intended checkout or install.

## What Not To Do

- Do not call CPU-only import success an acceptable replacement for CUDA training/rendering.
- Do not install every optional tool when the task only needs one workflow.
- Do not start SIBR builds, full training, or dataset downloads as an environment smoke check.
- Do not mix incompatible PyTorch/CUDA/compiler variants in one prefix; create a new environment if the dependency direction changes.
