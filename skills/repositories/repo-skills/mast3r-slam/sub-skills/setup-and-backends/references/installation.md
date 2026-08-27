# Installation and Backend Setup

## When to read

Read this when you need to create, repair, or re-verify the MASt3R-SLAM
runtime environment.

## Verified install shape

The inspected, working environment used:

- Python 3.11.
- PyTorch 2.5.1 with CUDA 12.4.
- A CUDA toolkit/nvcc path available to the build.
- `cuda-cudart-dev` and `cuda-cccl` so the root CUDA extension can find
  `cuda_runtime.h`.
- `ninja` to speed up local extension builds.
- Editable installs for `thirdparty/mast3r`, `thirdparty/in3d`, and the root
  MASt3R-SLAM package.
- `opencv-python==4.10.0.84` because the repo pins `numpy==1.26.4` and the
  newer OpenCV 5 wheel requires NumPy 2.

## Recommended install order

Use a private prefix. Substitute your own prefix and checkout path.

```bash
conda create --yes --prefix <prefix> python=3.11 pip
conda install --yes --prefix <prefix> -c pytorch -c nvidia \
  pytorch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 pytorch-cuda=12.4 \
  cuda-nvcc=12.4
conda install --yes --prefix <prefix> -c nvidia cuda-cudart-dev=12.4 cuda-cccl=12.4
conda install --yes --prefix <prefix> ninja
conda install --yes --prefix <prefix> 'mkl<2025' 'intel-openmp<2025'
```

Then prepare the source tree:

```bash
git submodule update --init --recursive
```

Install the third-party packages and then the root package:

```bash
conda run --prefix <prefix> python -m pip install --no-build-isolation -e <repo-root>/thirdparty/mast3r
conda run --prefix <prefix> python -m pip install -e <repo-root>/thirdparty/in3d
conda run --prefix <prefix> bash -lc 'CUDA_HOME=<prefix> TORCH_CUDA_ARCH_LIST=8.0 MAX_JOBS=4 python -m pip install --no-build-isolation -e <repo-root>'
conda run --prefix <prefix> python -m pip install --force-reinstall --no-deps opencv-python==4.10.0.84
```

If you prefer pip-only setup, keep the same build-tool and CUDA-header
requirements. The repo still needs a real CUDA build toolchain; a CPU-only torch
wheel is not enough.

## Minimal verification order

1. `python -m pip check`
2. `python -I -c "from importlib import metadata; print(metadata.version('MAST3R-SLAM'))"`
3. From the generated skill root, `python scripts/check_install.py --check-cuda`
4. `python main.py --help`
5. If checkpoints are present, rerun `check_install.py --checkpoint-dir <dir>`

## Notes on installed package facts

- `mast3r_slam_backends` is a compiled extension built from the root checkout.
- `mast3r.utils.path_to_dust3r` must run before direct `dust3r` imports.
- `evo` is required for evaluation outputs; `pyrealsense2` is optional unless
  you need live camera input.
- `torchcodec` is optional and only accelerates MP4 loading.
- Visualization imports `in3d`, `moderngl`, `glfw`, and `imgui`.
