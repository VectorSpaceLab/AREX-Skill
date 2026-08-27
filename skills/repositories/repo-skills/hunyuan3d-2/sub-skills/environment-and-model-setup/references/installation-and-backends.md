# Installation and Backend Setup

## Package identity

- Distribution/package import: `hy3dgen`
- Inspected version: `2.0.2`
- Repository URL in package metadata: `https://github.com/Tencent/Hunyuan3D-2`
- Primary runtime dependencies: PyTorch, torchvision, diffusers, transformers, trimesh, pymeshlab, pygltflib, xatlas, accelerate, gradio, fastapi, uvicorn, rembg, onnxruntime, ninja, pybind11, OpenCV, omegaconf, tqdm.

## Recommended install order

Use an isolated Python environment. The exact manager can be Conda, micromamba, uv/venv, or another controlled environment, but CUDA and compiler compatibility matter.

```bash
# 1. Install PyTorch for the target CUDA/host first.
python -m pip install torch torchvision --index-url <matching-pytorch-index>

# 2. Install Hunyuan3D package requirements and package source.
# If you are working in a package checkout, install its requirements/package there.
python -m pip install -r <hunyuan3d-package-source>/requirements.txt
python -m pip install -e <hunyuan3d-package-source>

# 3. Build texture extensions when texture workflows are in scope.
python -m pip install --no-build-isolation <hunyuan3d-package-source>/hy3dgen/texgen/differentiable_renderer
python -m pip install --no-build-isolation <hunyuan3d-package-source>/hy3dgen/texgen/custom_rasterizer
```

Upstream README-style instructions may use `python3 setup.py install` inside extension directories; `pip install --no-build-isolation <dir>` is usually easier to reproduce and keeps the active environment explicit.

## Verified backend class

This skill's production environment verified a CUDA backend with:

- Python 3.11.
- `hy3dgen==2.0.2`.
- `torch==2.7.1+cu128` and `torchvision==0.22.1+cu128`.
- CUDA-capable NVIDIA A100 GPUs.
- `pip check` passing.
- `mesh_processor` and `custom_rasterizer` built/imported.
- `MeshRender(device="cuda")` constructed.

The runtime skill intentionally does not embed local environment paths. Future agents should reproduce equivalent backend properties, not copy the private prefix.

## Meaningful smoke checks

Basic package check:

```bash
python scripts/check_install.py --json
```

CUDA check:

```bash
python scripts/check_install.py --check-cuda --json
```

Texture extension check:

```bash
python scripts/check_install.py --check-cuda --check-extensions --json
```

Direct Python smoke:

```python
import torch
from importlib.metadata import version
print(version("hy3dgen"))
print(torch.cuda.is_available())
if torch.cuda.is_available():
    torch.empty((1,), device="cuda")

import hy3dgen.shapegen, hy3dgen.texgen
import mesh_processor, custom_rasterizer
from hy3dgen.texgen.differentiable_renderer.mesh_render import MeshRender
MeshRender(device="cuda")
```

Import `torch` before direct `custom_rasterizer` import.

## Backend policy

| Capability | Required backend | CPU substitute |
| --- | --- | --- |
| Hunyuan3D-DiT shape generation | CUDA | none verified |
| FlashVDM decoding | CUDA | none verified |
| Hunyuan3D-Paint texture generation | CUDA + texture extensions | none verified |
| VAE encode/decode | CUDA | none verified |
| API/Gradio parser checks | any | full |
| Client payload dry-runs | any | full |
| Package import/static docs checks | any | partial, not inference proof |

Do not convert CUDA generation failures into a CPU fallback claim. CPU checks are useful for guidance validation, not for proving generation.

## Extension build prerequisites

- C++ compiler and `ninja`/`pybind11`.
- CUDA toolkit/compiler compatible with PyTorch CUDA.
- CUDA development headers/libraries, including headers such as `cusparse.h`.
- A compatible `TORCH_CUDA_ARCH_LIST` for the target GPU can reduce build cost and avoid compiling unnecessary architectures.

If build isolation creates a fresh environment without PyTorch, use `--no-build-isolation` so the extension sees the installed torch/CUDA configuration.

## OpenGL/pymeshlab runtime

`pymeshlab` can require `libOpenGL.so.0` even in headless environments. Install an OpenGL runtime package inside or visible to the active environment when mesh cleanup emits plugin warnings or import errors.

## Stale docs warning

Some source documentation pages in the distilled checkout contained stale placeholder text unrelated to Hunyuan3D. Prefer README-derived install guidance, package metadata, extension setup facts, and this skill's references.
