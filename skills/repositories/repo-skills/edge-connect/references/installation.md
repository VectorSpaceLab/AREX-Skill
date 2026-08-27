# Installation

## Purpose

Read this before creating an environment or inspecting live APIs for EdgeConnect. The repository is a legacy PyTorch and scientific-Python stack, so modern defaults can break `src.config.Config`, image loading, or the Canny/metrics paths.

## When to read

- before installing dependencies
- before running `scripts/check_env.py`
- before changing PyYAML, SciPy, scikit-image, or OpenCV versions
- before trying to run the training or testing wrappers in a fresh environment

## Known-good baseline

One verified working baseline is:

- Python 3.7
- NumPy 1.19.5
- SciPy 1.2.1
- scikit-image 0.14.2
- matplotlib 2.2.3
- Pillow 9.4.0 or another compatible Pillow build
- OpenCV 3.4.2
- future 0.18.3
- pyaml 23.5.8
- PyYAML 5.4.1
- torch 1.13.1+cu117
- torchvision 0.14.1+cu117

The exact CUDA wheel tag can vary with host drivers, but the repo needs a CUDA-enabled Torch build for the normal GPU workflow.

## Example setup

Use a private prefix and install the legacy scientific stack before the Torch wheels:

```bash
conda create --yes --prefix <prefix> "python=3.7" pip
conda install --yes --prefix <prefix> "numpy=1.19" "scipy<1.3" "scikit-image=0.14" "matplotlib=2.2" pillow opencv pyyaml future
conda run --prefix <prefix> python -m pip install --no-cache-dir "torch==1.13.1+cu117" "torchvision==0.14.1+cu117" --extra-index-url https://download.pytorch.org/whl/cu117
conda run --prefix <prefix> python -m pip install pyaml "PyYAML==5.4.1"
```

If Conda cannot solve the Torch package combination directly, install the legacy scientific packages first and then use the PyTorch wheel index with pip. This repo is old enough that a conda-only solve often conflicts on Python or OpenCV/BLAS pins.

## Why PyYAML matters

`src/config.py` calls `yaml.load(...)` without a Loader argument. That works with PyYAML 5.4.x but raises a `TypeError` with PyYAML 6.x. If you see:

```text
TypeError: load() missing 1 required positional argument: 'Loader'
```

your YAML package is too new for the current source code. Pin PyYAML < 6 or patch the loader call.

## Smoke check

After installing, run the bundled checker from a neutral working directory:

```bash
python scripts/check_env.py --repo-root <EdgeConnect checkout> --cuda
```

Use `--cuda` on a GPU host to confirm the Torch wheel, driver, and tiny device allocation. Omit `--cuda` if you only need CPU importability.

## Notes

- `requirements.txt` is not a complete install story by itself because the repo expects a separate Torch installation.
- `train.py --help` and `test.py --help` are not ideal environment smoke checks because the wrappers enter `main()` and can create checkpoint directories as a side effect.
- Keep the environment private and reusable; do not mutate a user-owned Python prefix unless that was explicitly authorized.
