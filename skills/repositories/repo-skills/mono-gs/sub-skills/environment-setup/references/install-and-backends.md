# Install and backends

This guide prepares a MonoGS checkout for CUDA-backed imports and later operating workflows.

## Reference baseline
- Python 3.7.13
- PyTorch 1.12.1 / torchvision 0.13.1 / torchaudio 0.12.1
- CUDA runtime 11.6
- `plyfile`, `opencv-python`, `munch`, `trimesh`, `evo`, `open3d`, `torchmetrics`, `imgviz`, `PyOpenGL`, `glfw`, `PyGLM`, `wandb`, `lpips`, `rich`, `ruff`
- compiled native extensions: `simple_knn` and `diff_gaussian_rasterization`
- optional live-demo package: `pyrealsense2`

## 1) Initialize the submodules
The extension sources must be present before any environment install or rebuild.

```bash
git submodule update --init --recursive
git submodule status
```

Both extension directories should contain their `setup.py` and CUDA sources after this step.

## 2) Create or refresh the conda environment
Use the repo manifest as the base install route.

```bash
conda env create -f environment.yml
conda activate MonoGS
```

If the environment already exists, reactivate it and continue with the native rebuild steps below.

## 3) Confirm CUDA visibility and the compiler toolchain
MonoGS is not CPU-only. Core imports and the renderer expect CUDA to be visible.

```bash
nvidia-smi
nvcc --version
python - <<'PY'
import torch
print(torch.__version__)
print(torch.version.cuda)
print(torch.cuda.is_available())
if torch.cuda.is_available():
    x = torch.zeros(1, device="cuda")
    print(x.device)
PY
```

If `nvcc` is missing, install a CUDA toolkit that includes the compiler or use a toolkit-dev package, then set `CUDA_HOME` to that toolkit root before rebuilding the extensions.

## 4) Build the CUDA extensions
Build the KNN extension first, then the rasterizer extension.

```bash
export MAX_JOBS="${MAX_JOBS:-4}"
export CUDA_HOME="${CUDA_HOME:-/usr/local/cuda-11.6}"  # set this to your toolkit root
python -m pip install -e submodules/simple-knn --no-build-isolation -v
python -m pip install -e submodules/diff-gaussian-rasterization --no-build-isolation -v
```

The native import surface depends on both compiled modules:
- `gaussian_splatting.scene.gaussian_model` imports `simple_knn._C`
- `gaussian_splatting.gaussian_renderer` imports `diff_gaussian_rasterization`

## 5) Smoke the core MonoGS imports
Use the import smoke to confirm the native modules and the CUDA path are ready.

```bash
python - <<'PY'
import simple_knn._C
import diff_gaussian_rasterization
from gaussian_splatting.scene.gaussian_model import GaussianModel
from gaussian_splatting.gaussian_renderer import render
print("core MonoGS imports ok")
PY
```

If this fails, stop and use the troubleshooting reference before trying any run command.

## 6) Confirm GUI dependencies
The GUI path uses Open3D, OpenGL, GLFW, and imgviz.

```bash
python - <<'PY'
import open3d as o3d
import open3d.visualization.gui as gui
import open3d.visualization.rendering as rendering
from OpenGL import GL
import glfw
import imgviz
print("GUI imports ok")
PY
```

A valid OpenGL driver and display stack are still required for window creation. On headless hosts, imports can succeed while the window backend still fails.

## 7) Optional RealSense support
Install this only if you need the live camera path.

```bash
python -m pip install pyrealsense2
python - <<'PY'
try:
    import pyrealsense2
    print("pyrealsense2 ok")
except Exception as exc:
    print("pyrealsense2 optional:", exc)
PY
```

If the package is absent, offline SLAM and evaluation can still be prepared.

## 8) Run the bundled environment checker
From this sub-skill directory, run:

```bash
python ../../scripts/check_monogs_environment.py
```

A healthy report should confirm:
- CUDA is visible
- a CUDA tensor can be allocated
- `simple_knn._C` imports
- `diff_gaussian_rasterization` imports
- `gaussian_splatting.scene.gaussian_model` imports
- `gaussian_splatting.gaussian_renderer` imports
- GUI imports succeed when the GUI packages are installed
