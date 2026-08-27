# Installation

This repo is a TensorFlow 1.x template application. The public install surface is intentionally small:

- Python 3.7 is the safest target for the pinned TensorFlow 1.15.5 stack.
- The package name exposed by `setup.py` is `trainer`.
- There are no console entry points in `setup.py`; use the bundled scripts directly.

## Recommended core environment

Install the TF1-era stack first:

```bash
python -m pip install tensorflow==1.15.5 numpy<1.19 scipy<1.8 scikit-learn<1.1 coloredlogs>=5.2 protobuf==3.20.3
python -m pip install -e .
```

That core set supports:

- dense and sparse training scripts
- TFRecords conversion and inspection
- TensorBoard event inspection
- the shared model and utility modules

## Serving-client add-ons

If you also want the Python TensorFlow Serving helpers and the minimal benchmark gRPC modes, add:

```bash
python -m pip install grpcio==1.32.0 grpcio-tools==1.32.0 tensorflow-serving-api==1.15.0
```

Those packages are not required for the pure data/training workflow, but they are needed for the serving sub-skill's live gRPC path.

## Legacy reference-only add-ons

Only install these when you are intentionally exploring the legacy surfaces:

- `Django==1.9.*` for the old HTTP wrapper
- `pydicom` for the DICOM-to-CSV example
- `maven`, `scala`, `spark`, `go`, `bazel`, Android Studio, or Xcode for the non-Python clients

The generated skill treats those surfaces as reference-only because they depend on external toolchains.

## Quick environment check

After installation, run the bundled smoke check:

```bash
python scripts/check_tf1_environment.py
```

Use the serving check when you installed the gRPC extras:

```bash
python scripts/check_tf1_environment.py --check-serving
```

## Compatibility notes

- TensorFlow 2.x is not a compatible default for this repo because the source uses `tf.contrib`, `tf.app.flags`, and `tf.python_io`.
- The dense and sparse trainer modules register global flags at import time, so they should be run in separate Python processes.
- The serving helpers use the public `tensorflow_serving.apis` modules when the serving add-ons are installed.
