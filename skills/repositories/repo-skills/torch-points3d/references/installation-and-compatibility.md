# Installation and Compatibility

## Purpose

Read this when setting up Torch Points3D, choosing CPU/GPU/sparse backends,
checking an import failure, or deciding whether a modern environment is too new
for the repository snapshot captured by this skill.

## Package and version facts

- Public package/import: distribution `torch-points3d` / import package `torch_points3d`.
- Snapshot package version: `0.2.0`.
- Package metadata requires Python `^3.7`, `torch ~=1.8.0`, `torch-geometric ^1.7.1`, `torch-scatter ^2.0.0`, `torch-sparse >=0.6.10,<0.6.13`, `torch-cluster ^1.5.6`, `torch-points-kernels ^0.7.0`, `hydra-core ~1.0.0`, `omegaconf 2.0.x`, `numpy <1.20.0`, `open3d 0.12.0`, `scikit-image ^0.16.2`, and legacy logging/data packages such as W&B, TensorBoard, gdown, plyfile, laspy, and torchnet.
- Installed-package inspection for this skill verified CPU imports against Python 3.8, PyTorch 1.8.1+cpu, PyG 1.7.2 CPU extension wheels, Hydra 1.0.7, OmegaConf 2.0.6, and torch-points-kernels 0.7.0. This verifies the selected CPU-required scope only; it is not proof that CUDA or sparse backends run.

## Recommended setup order

1. Create an isolated legacy Python environment. Python 3.8 is a practical target for old wheels; Python 3.10+ commonly conflicts with pinned NumPy/Numba/Open3D requirements.
2. Install a PyTorch build first. Choose CPU, CUDA, or ROCm to match the actual target hardware.
3. Install PyG extension wheels compiled for exactly that PyTorch/CUDA combination.
4. Install Torch Points3D and runtime dependencies.
5. Run the bundled environment probe and one workflow-specific smoke test before training or downloading data.

Example CPU-oriented sequence:

```bash
python -m pip install "pip<25"
python -m pip install "torch==1.8.1+cpu" "torchvision==0.9.1+cpu" \
  --index-url https://download.pytorch.org/whl/cpu
python -m pip install "torch-scatter==2.0.8" "torch-sparse==0.6.12" \
  "torch-cluster==1.5.9" "torch-geometric==1.7.2" \
  -f https://data.pyg.org/whl/torch-1.8.1+cpu.html
python -m pip install "hydra-core==1.0.7" "omegaconf==2.0.6" "numpy<1.20" \
  "protobuf<3.20" "googledrivedownloader==0.4" torch-points3d
python scripts/torch_points3d_env_probe.py --json --require-package --require-pyg
```

The exact PyTorch wheel URL and PyG wheel page must change for CUDA builds. Do
not mix CPU PyTorch with CUDA extension wheels or CUDA PyTorch with CPU-only
extensions when a workflow needs compiled PyG operators.

## Optional backend matrix

| Capability | Package/backend | Required for selected CPU scope? | Notes |
| --- | --- | --- | --- |
| Dense PointNet2/RSConv high-level API | PyTorch + PyG dense/message-passing ops | Yes | CPU smoke is sufficient for basic API and config guidance. |
| KPConv partial-dense API | `torch-points-kernels` + PyG compiled ops | Yes for KPConv guidance, but CPU extension may need source-build fixes | Build failures often come from old C++ extension assumptions on newer compilers. |
| SparseConv3d high-level API | `MinkowskiEngine` or `torchsparse` | Optional | Constructor defaults to `backend="minkowski"`; set `backend="torchsparse"` or `SPARSE_BACKEND` only after backend import works. |
| Minkowski application model | `MinkowskiEngine` | Optional | Importing `torch_points3d.applications.minkowski` raises `ModuleNotFoundError` if MinkowskiEngine is absent. |
| CUDA acceleration | matching CUDA PyTorch/PyG/extension wheels | Optional for CPU-capable workflows | Required only when the user asks for CUDA-only performance or tests. |
| Registration visualization/classical baselines | `open3d`, dataset fragments, feature files | Workflow-specific | Open3D import alone is not enough; data and checkpoint files are also required. |
| W&B checkpoint downloads/pretrained registry | network + W&B-hosted URLs | Optional | `PretainedRegistry.from_pretrained(download=True)` can download from remote URLs. Use `download=False` only for tag discovery; it returns no model. |

## Minimal verification snippets

Package and dependency import:

```bash
python - <<'PY'
import torch
import torch_points3d
import torch_geometric, torch_scatter, torch_sparse, torch_cluster
print("torch", torch.__version__, "cuda", torch.cuda.is_available())
print("torch_points3d", torch_points3d.__name__)
PY
```

Application API signature sanity:

```bash
python - <<'PY'
import inspect
from torch_points3d.applications.pointnet2 import PointNet2
from torch_points3d.applications.kpconv import KPConv
from torch_points3d.applications.rsconv import RSConv
from torch_points3d.applications.sparseconv3d import SparseConv3d
for fn in [PointNet2, KPConv, RSConv, SparseConv3d]:
    print(fn.__name__, inspect.signature(fn))
PY
```

Optional sparse backend probe:

```bash
python - <<'PY'
for name in ["MinkowskiEngine", "torchsparse", "pycuda"]:
    try:
        __import__(name)
        print(name, "available")
    except Exception as exc:
        print(name, "unavailable:", type(exc).__name__)
PY
```

## Compatibility gotchas

- OmegaConf 2.0.6 has legacy dependency metadata that newer `pip` versions may reject. If installation fails on metadata parsing, use a pip version that still accepts the legacy specifier or install from a resolved lock-compatible environment.
- TensorBoard 2.6-era code is incompatible with newer protobuf 4.x in many environments. Pin `protobuf<3.20` if TensorBoard import fails with descriptor errors.
- `googledrivedownloader` is the import name expected by PyG 1.7 datasets; package versions with a different import surface can break Torch Points3D imports through `torch_geometric.datasets`.
- `torch-points-kernels` may need a source build when wheels are unavailable. Treat local compiler flags as environment-specific troubleshooting, not a universal install command.
- The package does not expose a modern CLI entry point. Repo checkout scripts such as `train.py`, `eval.py`, and forward inference scripts are Hydra programs that require the checkout-style `conf/` tree or an equivalent copied config tree.
