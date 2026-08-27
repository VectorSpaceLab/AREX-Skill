# Environment and installation

Use this reference before installing or diagnosing detrex. It summarizes the public install contract and safe verification checks.

## Requirements

- Linux with Python 3.7 or newer. For modern PyTorch/Detectron2 stacks, prefer a Python version supported by the selected wheels.
- PyTorch 1.10+ and a matching torchvision build.
- Detectron2 installed for the same Python/PyTorch/CUDA stack.
- Compiler toolchain for source builds; ninja is optional but useful.
- CUDA runtime/toolkit and `CUDA_HOME` when building detrex's custom CUDA operator for `MultiScaleDeformableAttention`.

## Source install shape

A typical source install is:

```bash
git clone https://github.com/IDEA-Research/detrex.git
cd detrex
git submodule init
git submodule update
python -m pip install -e detectron2
python -m pip install -e .
```

If the build isolation environment cannot import the already-installed PyTorch while building detrex, use an explicit no-build-isolation install after confirming PyTorch is installed in the target environment:

```bash
CUDA_HOME=<cuda-toolkit-root> TORCH_CUDA_ARCH_LIST="8.0" python -m pip install --no-build-isolation -e .
```

Set `TORCH_CUDA_ARCH_LIST` to match the target GPU family when compiling locally. Do not use the example value blindly.

## Minimal validation

From the intended runtime environment:

```bash
python -c "import torch, torchvision; print(torch.__version__, torchvision.__version__, torch.cuda.is_available())"
python -c "import detectron2; import detrex; print('imports ok')"
python -c "from detrex.config import get_config; print(get_config('common/train.py').train.device)"
```

Use the bundled checker for more structured output:

```bash
python scripts/check_environment.py --strict --check-config common/train.py
python scripts/check_environment.py --strict --check-cuda-extension
python scripts/check_environment.py --tool-help train analyze demo
python scripts/check_environment.py --tool-help hydra --repo-root <detrex-checkout>
```

## CUDA extension expectations

The custom extension is required for CUDA-backed multi-scale deformable attention. It is relevant to Deformable-DETR, DINO, and other multi-scale deformable-attention models.

A healthy extension check means:

- `torch.cuda.is_available()` is true for CUDA workflows.
- `detrex._C` imports successfully.
- The extension exposes `ms_deform_attn_forward` and `ms_deform_attn_backward`.

If `detrex._C` fails to import, CPU-safe tasks may still work, but do not claim Deformable/DINO CUDA operator readiness.

## Dependency pitfalls

| Dependency surface | Why it matters |
|---|---|
| `pkg_resources` / setuptools | detrex config helper imports `pkg_resources`; very new packaging stacks can omit it. |
| `timm` | required for `TimmBackbone` and many DINO backbone variants. |
| `wandb` | imported by detrex WandB writer and used only when WandB logging is enabled. |
| `submitit`, `hydra-core`, `omegaconf` | needed for Hydra/Slurm launcher workflows. |
| `opencv-python` / `cv2` | needed for demos and visualization tools. |
| `pybind11`, CUDA toolkit/compiler | needed when building C++/CUDA extension from source. |

## Verification boundaries

Passing imports does not mean full model training/evaluation is ready. Full runs also need datasets, local checkpoints, matching config/model families, available GPUs for CUDA configs, and sufficient time. Treat downloads and long training/evaluation as separate user-approved steps.

The Hydra launcher resolves `configs/hydra` relative to a detrex source checkout in this release. If `python -m tools.hydra_train_net --help` fails from a wheel-style install with a missing `configs/hydra` directory, validate it from a source checkout with `--repo-root <detrex-checkout>` or use the bundled command builder for dry-run command construction.
