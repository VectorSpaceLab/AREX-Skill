# Installation and environment notes

## Recommended setup

Use an isolated Python 3.11 environment. For normal package use, install the published package plus the direct runtime imports that this version uses but does not fully declare as direct dependencies.

```bash
python -m pip install "imagededup==0.3.3.post2" numpy scipy
```

If you are intentionally working inside a separate source checkout, an editable install is also fine after installing runtime dependencies, but the runtime workflows in this skill do not require any original checkout files.

## Why the extra packages matter

- `numpy` is used throughout hashing, CNN preprocessing, image utilities, evaluation helpers, and tests.
- `scipy` is required by the DCT-based perceptual hash path.
- `torch` and `torchvision` are required for the CNN workflow and custom model support.
- `PyWavelets`, `scikit-learn`, `matplotlib`, `Pillow`, and `tqdm` are all part of the runtime surface.

## Runtime behavior to expect

- `CNN()` selects CUDA automatically when `torch.cuda.is_available()` is true; otherwise it falls back to CPU.
- The default CNN backbone is MobileNetV3 Small.
- The first default `CNN()` instantiation may download pretrained weights from the PyTorch model host if they are not already cached.
- The hash workflows do not require GPU support.
- There is no CLI entry point; the install surface is API-first.

## Verification checks worth running after install

```bash
python -m pip check
python -I -c "from imagededup.methods import PHash, CNN; from imagededup.evaluation import evaluate; from imagededup.utils import plot_duplicates, CustomModel"
```

## When install problems usually mean something else

- `ModuleNotFoundError: numpy` or `ModuleNotFoundError: scipy` usually means the environment was created from incomplete direct dependency metadata and needs the explicit packages above.
- A failing `CNN()` instantiation can mean missing `torch` / `torchvision`, a bad model-cache state, or blocked access to pretrained weights.
- A failing CUDA expectation usually means the active torch build or host does not expose CUDA to `torch.cuda.is_available()`.
- A Cython-extension failure while installing from a source checkout usually means build dependencies are missing or stale, not that the API surface changed.