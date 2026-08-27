# Installation and Compatibility

## Purpose

Read this when setting up or repairing a `textgenrnn` runtime. The repository is small, but its import path is sensitive to TensorFlow/Keras and setuptools compatibility.

## Verified stack

The environment used to inspect this repository successfully imported and exercised `textgenrnn` with:

- Python 3.11
- `textgenrnn==2.0.0`
- `tensorflow==2.15.1`
- `keras==2.15.0`
- `numpy==1.26.4`
- `scikit-learn==1.9.0`
- `h5py==3.14.0`
- `tqdm==4.70.0`
- `setuptools==80.10.2`

The important compatibility boundary is that this repository still imports `pkg_resources` and `tensorflow.compat.v1.keras.backend.set_session`. A modern TensorFlow/Keras 3 stack is not a safe default for this package.

## Recommended install patterns

### Published package

```bash
python -m pip install textgenrnn
```

If the runtime already uses a pre-Keras-3 TensorFlow stack, this may be enough.

### Local checkout validation

When validating a local checkout, install the checkout itself inside a compatible environment and then pin the compatibility boundary if needed:

```bash
python -m pip install -e .
python -m pip install 'tensorflow==2.15.1' 'setuptools<81'
```

If you start with a fresh environment, install the package dependencies first or let `pip` resolve them during the editable install. The verified stack above is the safest baseline.

## Minimal validation sequence

1. Confirm the import path works:

```bash
python -c "from textgenrnn import textgenrnn; print(textgenrnn.__name__)"
```

2. Confirm TensorFlow exposes the compatibility API this repository uses:

```bash
python -c "import tensorflow as tf; import tensorflow.compat.v1.keras.backend as K; print(tf.__version__); print(hasattr(K, 'set_session'))"
```

3. Confirm `pkg_resources` is available:

```bash
python -c "import pkg_resources; print(pkg_resources.__file__)"
```

4. Run the bundled environment helper if you want a quick model-load/generation smoke:

```bash
python scripts/check_textgenrnn_env.py --generate --n 1 --max-gen-length 20
```

## What to expect from GPU support

- GPU acceleration is optional, not required, for the selected package workflows.
- The host machine used for inspection exposed NVIDIA GPUs, but the validated Python environment still ran on CPU because CUDA libraries were not available to TensorFlow.
- If you need CUDA acceleration later, use a TensorFlow build and CUDA runtime that cooperate with this package's pre-Keras-3 API surface. The generated skill does not require that backend to be available by default.

## When installation fails

If import fails with `pkg_resources` or `tensorflow.compat.v1.keras` errors, treat the runtime as incompatible, not as a package bug. Repair the environment first, then retry the import check.
