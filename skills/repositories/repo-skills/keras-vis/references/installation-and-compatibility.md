# Installation and Compatibility

## Purpose

Read this before installing or repairing keras-vis. The release is legacy and depends on standalone Keras plus TensorFlow 1.x graph mode.

## Verified baseline

The generated skill was verified on:

- Python 3.7
- `keras-vis` 0.5.0
- `Keras` 2.2.4
- `tensorflow` 1.15.5
- `protobuf` 3.20.3
- `numpy` 1.18.5
- `scipy` 1.5.4
- `h5py` 2.10.0
- `scikit-image` 0.16.2
- `matplotlib` 3.3.4
- optional `Pillow` and `imageio`

## Recommended install path

Use a Python 3.7 environment when possible. Newer Python and TensorFlow releases are not a good fit for this codebase because the package uses legacy standalone Keras and TensorFlow 1.x graph APIs.

A known-good install recipe is:

```bash
python -m pip install \
  "keras-vis==0.5.0" \
  "Keras==2.2.4" \
  "tensorflow==1.15.5" \
  "protobuf<=3.20.3" \
  "numpy==1.18.5" \
  "scipy==1.5.4" \
  "h5py==2.10.0" \
  "scikit-image==0.16.2" \
  "matplotlib==3.3.4" \
  "importlib-metadata" \
  Pillow imageio
```

If you are working from a checkout instead of PyPI, install the local package after the dependency pins are in place.

## Compatibility notes

- Use standalone `keras`, not `tensorflow.keras`.
- Expect TensorFlow graph-mode behavior, especially for guided/rectified backprop modifiers.
- `protobuf` newer than 3.20.x commonly breaks TensorFlow 1.15 import paths with `Descriptors cannot not be created directly`.
- `Pillow` and `imageio` are optional for the core visualization APIs but are required for text drawing and GIF callbacks.
- CUDA is optional for this skill's selected workflows; the bundled smoke checks are CPU-based and do not require a GPU.
- Theano appears in the source tree as a legacy alternative, but the generated skill does not require it for its verified workflows.

## Minimal import check

After install, verify the public package imports:

```bash
python -c "import vis; import keras; import tensorflow; from vis.visualization import visualize_saliency; print('ok')"
```

If that fails, read [troubleshooting.md](troubleshooting.md) before changing workflow code.

## When to read this file

- Before creating or repairing a private inspection environment.
- After a resolver upgrades TensorFlow, protobuf, or Keras unexpectedly.
- When a smoke script reports an import error that looks like a dependency mismatch rather than a code bug.
