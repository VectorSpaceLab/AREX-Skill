# Installation and Environment

Read this when a task requires installing or checking the Waymo Open Dataset package before using any sub-skill.

## Verified package line

The repository build metadata identifies the primary distribution as `waymo-open-dataset-tf-2-12-0` version `1.6.7`, importing as `waymo_open_dataset`. It declares Python-package dependencies such as TensorFlow 2.13, TensorFlow Probability 0.21, NumPy 1.23.5, pandas 1.5.3, Dask 2023.3.1, PyArrow 16.0.0, JAX/JAXlib 0.4.13, visu3d 1.5.1, and dacite 1.8.1.

A robust CPU inspection install is:

```bash
python -m pip install -f https://storage.googleapis.com/jax-releases/jax_releases.html \
  waymo-open-dataset-tf-2-12-0==1.6.7
```

Use Python 3.10 when possible for this exact package line. Python 3.11 may fail dependency resolution because public package indexes no longer expose a compatible `jaxlib==0.4.13` wheel for that interpreter. If the user must use a newer Python, first check whether a newer WOD wheel exists for the TensorFlow version they need.

## Minimal smoke check

```bash
python - <<'PY'
from importlib.metadata import version
from waymo_open_dataset import v2
from waymo_open_dataset.metrics.python import config_util_py
print('WOD distribution:', version('waymo-open-dataset-tf-2-12-0'))
print('V2 tags:', v2.ALL_TAGS[:5])
print('config util:', config_util_py.__name__)
PY
```

Or use the bundled helper:

```bash
python scripts/check_wod_environment.py --json
```

## Optional GPU and challenge timing

The main package and most utility/metric workflows can be inspected with a CPU TensorFlow installation. GPU is optional for this skill unless the current task explicitly requires challenge model timing, GPU TensorFlow execution, or a user model container. If TensorFlow prints that CUDA libraries are missing, do not call CUDA verified; either proceed with CPU-only WOD API work or prepare a separate GPU-capable TensorFlow environment for the specific task.

## Optional Deeplab2 camera segmentation

The camera segmentation metric path imports `deeplab2` in addition to WOD. The repository provides a setup script for that optional package, but it performs external installation/build work and was not part of the verified baseline. Use [../sub-skills/camera-and-segmentation/references/troubleshooting.md](../sub-skills/camera-and-segmentation/references/troubleshooting.md) before enabling it.

## Docker and notebooks

The repository documents a CPU Jupyter container for tutorials and a separate Docker path for wheel building. Treat these as environment workflows, not requirements for ordinary package use. Notebook examples often require downloaded WOD data, visualization support, or challenge assets; use their distilled recipes in this skill rather than assuming the notebooks are runnable in the current environment.
