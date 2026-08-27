# Installation and Optional Dependencies

MONAI is a PyTorch-based Python package. The base package metadata requires Python 3.10 or newer, `torch>=2.8.0`, and `numpy>=1.24,<3.0`. Most medical-image IO, workflow engines, tracking, export, and high-level app features depend on optional packages.

## Base Install

Use the released package for normal application work:

```bash
pip install monai
```

Use an editable install only for local MONAI development or when a task explicitly targets a checkout:

```bash
pip install -e .
```

If a local editable install tries to build optional C++/CUDA extensions, check whether environment variables such as `BUILD_MONAI` or `FORCE_CUDA` were set intentionally. The default package path can inspect and use MONAI without building extensions.

## Optional Dependency Map

| Capability | Common optional packages | Notes |
| --- | --- | --- |
| NIfTI/medical image IO | `nibabel`, `itk`, `pynrrd`, `pydicom`, `h5py`, `zarr` | Install only the reader/writer formats required by the data. |
| PNG/JPEG/TIFF/WSI | `pillow`, `scikit-image`, `tifffile`, `imagecodecs`, `openslide-python`, `openslide-bin`, `cucim` | Whole-slide and GPU image IO may require system libraries or CUDA-specific wheels. |
| Training engines/handlers | `pytorch-ignite`, `tensorboard`, `tensorboardX`, `mlflow`, `clearml`, `psutil` | `monai.engines` and many handlers need Ignite or tracking extras. |
| Bundle CLI/config workflows | `fire`, `jsonschema`, `pyyaml`, `huggingface_hub` | Fire is required for `python -m monai.bundle` command dispatch. |
| Export/deployment | `onnx`, `onnxruntime`, TensorRT-related packages, `polygraphy` | Export paths often require checkpoints and backend-specific runtimes. |
| Auto3DSeg/HPO/apps | `nni`, `optuna`, `scipy`, `pandas`, app-specific packages | Training, HPO, and nnU-Net integration can be expensive and dependency-heavy. |
| Visualization | `matplotlib`, `tensorboard`, optional imaging packages | Verify GUI/headless constraints in notebooks or servers. |

Avoid installing MONAI's broad `all` extra unless the user explicitly needs broad development or integration coverage. Prefer route-specific dependencies so the environment remains predictable.

## Torch and Backend Choices

- CPU-only inspection and small smoke tests can use CPU Torch wheels.
- CUDA workflows need a Torch build compatible with the host driver and GPU architecture; verify `torch.cuda.is_available()` and a tiny tensor allocation before claiming CUDA support.
- TensorRT, CuCIM, and compiled extension paths are optional and more sensitive to Python, CUDA, compiler, and platform versions.
- MONAI APIs often work on CPU for development, but full 3D training/inference may require GPU memory planning.

## Quick Checks

```bash
python - <<'PY'
import importlib.util, monai, torch, numpy
print('monai', monai.__version__)
print('torch', torch.__version__, 'cuda', torch.cuda.is_available())
for name in ['nibabel', 'pydicom', 'ignite', 'fire', 'onnx', 'nni', 'optuna']:
    print(name, bool(importlib.util.find_spec(name)))
PY
```

Use `../scripts/check_monai_environment.py` for a reusable version of this check plus safe CLI-help probes.
