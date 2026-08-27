---
name: setup-and-backends
description: "Guides 3D Gaussian Splatting installation, CUDA extension builds,
  backend checks, and dependency troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Setup and Backends

Use this sub-skill when the task is about installing gaussian-splatting, deciding a CUDA/PyTorch/compiler combination, initializing submodules, checking imports, or diagnosing build/runtime backend errors before training or rendering.

## Read First

- Read [references/environment-guide.md](references/environment-guide.md) to choose a minimal environment, submodule, and system-tool setup.
- Read [references/backend-compatibility.md](references/backend-compatibility.md) when CUDA, PyTorch, compiler, GPU capability, or accelerated rasterizer compatibility is uncertain.
- Read [references/troubleshooting.md](references/troubleshooting.md) when installation, custom CUDA extension builds, imports, or optional tool checks fail.
- Run or adapt [scripts/check_backend.py](scripts/check_backend.py) for safe import/CUDA/extension/tool diagnostics. It does not run training or rendering.

## Required Mental Model

The repository is not a CPU-only Python package. Its primary optimizer, renderer, metrics, and Gaussian model code use CUDA tensors and custom CUDA extensions:

- `diff_gaussian_rasterization` supplies the differentiable renderer.
- `simple_knn` supplies CUDA distance computations for Gaussian initialization.
- `fused_ssim` is optional but used when installed for faster SSIM loss.
- PyTorch CUDA must be functional; a CPU import check is only a partial support-workflow check.

Do not claim training, rendering, or metric execution is verified unless CUDA and the required extensions import and a tiny CUDA allocation succeeds.

## Standard Setup Route

1. Confirm the user has a recursive clone or initialized submodules for the Python extensions. The SIBR viewer submodule is optional for Python workflows.
2. Choose one CUDA-capable Python environment for the Python optimizer/rendering stack. The README's historical environment uses Python 3.7, PyTorch 1.12.1, and CUDA 11.6; newer PyTorch/CUDA combinations can work, but extension builds must match the installed PyTorch CUDA runtime and compiler.
3. Install PyTorch with CUDA first, then runtime Python dependencies (`plyfile`, `tqdm`, `opencv-python`, `joblib`), then build/install the CUDA extensions from their submodule directories.
4. Run the bundled backend checker with `--require-cuda --require-extensions` before planning any native train/render verification.
5. Route prepared data questions to [../data-preparation/SKILL.md](../data-preparation/SKILL.md), training commands to [../training/SKILL.md](../training/SKILL.md), offline render/metrics to [../rendering-evaluation/SKILL.md](../rendering-evaluation/SKILL.md), and SIBR GUI operation to [../viewers/SKILL.md](../viewers/SKILL.md).

## Safe Preflight Pattern

```bash
python path/to/check_backend.py --repo-root /path/to/gaussian-splatting --require-cuda --require-extensions --tools
```

Interpretation:

- `PASS import diff_gaussian_rasterization`, `PASS import simple_knn._C`, and `PASS import fused_ssim` mean the Python extension modules import.
- `PASS tiny CUDA tensor allocation` means PyTorch can allocate on a visible CUDA device.
- Missing `colmap` or `magick` is not a Python stack failure unless the user is converting raw images.
- Missing SIBR build outputs is not a Python stack failure unless the user needs interactive viewers.

## Non-Goals

- Do not run `train.py`, `render.py`, `metrics.py`, or full evaluation here; those are final/native workflow checks after skill integration.
- Do not install broad development requirements or all optional components when the task only needs Python training/rendering.
- Do not mutate a user's existing environment without approval; prefer an isolated environment for repair attempts.
