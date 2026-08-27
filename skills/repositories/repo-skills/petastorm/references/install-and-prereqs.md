# Installation and Prerequisites

## Purpose

Read this before running bundled scripts or choosing a sub-skill. It summarizes the package metadata, extras, and runtime prerequisites
that matter for the current Petastorm checkout.

## Core install

The package metadata requires these core dependencies:

- `dill`
- `diskcache`
- `future`
- `numpy`
- `packaging`
- `pandas`
- `psutil`
- `pyspark`
- `pyarrow`
- `pyzmq`
- `six`
- `fsspec`
- `setuptools<70`

A standard install is still the right starting point:

```bash
pip install petastorm
```

For an editable checkout install, keep the same dependency floor and respect the `setuptools<70` pin.

## Optional extras

The package metadata defines these extras:

- `tf` for TensorFlow support
- `tf_gpu` for GPU TensorFlow support in older packaging layouts
- `torch` for PyTorch support
- `opencv` for compressed-image codecs
- `s3fs` for S3 filesystem handling
- `docs` for documentation builds
- `test` for maintainer test dependencies

Example combined install:

```bash
pip install "petastorm[tf,torch,opencv,s3fs]"
```

## Runtime prerequisites

- Spark-backed workflows need a working Java runtime that PySpark can use.
- TensorFlow workflows use `tensorflow.compat.v1` helpers in this repository snapshot.
- PyTorch workflows should import `pyarrow` before `torch`.
- OpenCV is only needed for image codecs and image-heavy examples.
- S3 and GCS workflows need the matching filesystem packages and credentials or mounts.

## Quick checks

- `scripts/check_install.py` verifies the core Petastorm import surface, reports missing optional extras, and checks that the console entry points are on PATH.
- `scripts/smoke_spark_session.py` verifies that a local Spark session can start.

## When to add extras

- Add `tf` or `tf_gpu` when the task needs `tf_tensors`, `make_petastorm_dataset`, or Spark-to-TensorFlow conversion.
- Add `torch` when the task needs `DataLoader`, `BatchedDataLoader`, `InMemBatchedDataLoader`, or Spark-to-PyTorch conversion.
- Add `opencv` when the task uses compressed image codecs or image-based examples.
- Add `s3fs` when the task uses `s3://` URLs.
