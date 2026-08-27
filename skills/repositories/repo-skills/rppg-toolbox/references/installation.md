# Installation and environment

Read this before importing or running the toolbox. It records the source-era
runtime contract without relying on the original setup script or a private
machine.

## Repository shape

The inspected revision has no root `setup.py` or `pyproject.toml` distribution
metadata. Its import roots are top-level `config.py`, `main.py`, `dataset`,
`neural_methods`, `unsupervised_methods`, and `evaluation`. Run commands from a
user-owned checkout root, or expose that checkout with an explicit
`PYTHONPATH`. Do not expect `pip install .` to create the application package.

## Tested construction baseline

The source requirements are pinned for a Python 3.8-era environment. The
verified inspection baseline used:

- Python 3.8.20;
- PyTorch 2.1.2 with CUDA 12.1, torchvision 0.16.2, and torchaudio 2.1.2;
- the pinned scientific/runtime requirements, including YACS, NumPy, SciPy,
  pandas, OpenCV, scikit-image, scikit-learn, timm, neurokit2, and mat73;
- `causal-conv1d` 1.0.0 and `mamba-ssm` 2.2.2 built with a compatible CUDA
  toolkit for the PhysMamba route.

A compatible NVIDIA driver and device are required for PhysMamba and for any
GPU claim. Other preprocessing, traditional methods, metrics, and some model
construction checks can use CPU, but a CPU import is not evidence of CUDA
execution.

## Safe setup sequence

1. Create a new isolated environment; do not remove or mutate an existing
   environment without explicit authorization.
2. Install the PyTorch build matching the selected backend before compiled
   extensions.
3. Install only the requirements needed by the selected routes. The original
   extension pins may be source distributions; if building them, make the
   CUDA toolkit, compiler, PyTorch version, and `--no-build-isolation` decision
   visible and use conservative build parallelism.
4. Run Python identity, `pip check`, import, and backend smoke checks.
5. Run the bundled config/model/unsupervised/visualization helpers before any
   dataset preprocessing or training.

The source setup helper removes and recreates environments or `.venv`; treat it
as a recipe to inspect, not as a harmless diagnostic. Do not install the
vendored language-model Mamba tree or its benchmark dependencies merely to use
rPPG-Toolbox's PhysMamba integration; the runtime contract needs the matching
public extension packages.

## First import checks

```bash
python -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available())"
python -c "import config, dataset, neural_methods, unsupervised_methods, evaluation; print('imports ok')"
```

For PhysMamba, additionally verify `mamba_ssm`, `causal_conv1d`, and `timm`,
then allocate a tiny CUDA tensor and run a small Mamba block. Read
[supervised-models/references/mamba-backend.md](../sub-skills/supervised-models/references/mamba-backend.md)
for the required-backend gate.

## Resource and safety limits

Raw datasets, pretrained weights, OpenFace, and motion-augmentation inputs are
external. Do not put them into the generated skill tree. Full preprocessing and
training can be multiprocess, memory-heavy, and write many files; begin with a
small user-owned fixture and retain the effective YAML/config identity.
