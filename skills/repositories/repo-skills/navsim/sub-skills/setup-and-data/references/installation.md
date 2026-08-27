# Installation and runtime prerequisites

## Supported baseline

NAVSIM v2 at package version `2.0.0` requires Python `>=3.9`. The published
environment definition uses Python 3.9 and pip 23.3.1. The dependency set
includes `nuplan-devkit` v1.2, Hydra 1.2, NumPy 1.23.4, Torch 2.0.1,
TorchVision 0.15.2, PyTorch Lightning 2.2.1, and the geospatial, image,
point-cloud, and serialization packages used by nuPlan/NAVSIM. Install the
backend-appropriate Torch build rather than replacing it casually: the
verified reference stack used CUDA 11.7-compatible Torch on an NVIDIA A100,
but CPU-only metadata and sensor-contract checks do not require CUDA.

The dependency declaration includes a Git-based nuPlan-devkit requirement.
Network access and licensing are therefore installation concerns, not data
validation concerns. Check the nuPlan/OpenScene license terms before acquiring
any dataset or map archive.

## Safe install sequence

Run these commands from the NAVSIM project root in a user-selected isolated
Python environment. They are installation commands only; they do not download
OpenScene data or run a benchmark.

```bash
python --version                         # expect 3.9 or newer
python -m pip install --upgrade pip
python -m pip install -e .
python -c "import navsim; print('navsim import OK')"
python -m pip check
```

If the project supplies a Conda environment definition, the equivalent
creation step is `conda env create -f environment.yml` followed by activation
and `python -m pip install -e .`. Do not mix a separately installed Torch,
TorchVision, and nuPlan stack into that environment without checking their
compatibility. If editable installation is not desired, install the released
`navsim==2.0.0` package and then verify the same imports; source/config
overrides still need to come from the matching NAVSIM v2 release.

A minimal import check can be split to localize failures:

```bash
python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
python -c "import nuplan; print('nuplan import OK')"
python -c "import navsim; print('navsim import OK')"
```

`pip check` should report no broken requirements. A Torch CUDA warning is not a
workspace-data failure; it becomes blocking only when the selected agent or
runner requires GPU execution.

## Required environment variables

Set these before importing code that builds maps or Hydra paths. Use absolute
paths and quote values containing spaces.

```bash
export NUPLAN_MAP_VERSION="nuplan-maps-v1.0"
export NUPLAN_MAPS_ROOT="/absolute/path/to/dataset/maps"
export NAVSIM_EXP_ROOT="/absolute/path/to/experiment-root"
export NAVSIM_DEVKIT_ROOT="/absolute/path/to/navsim-project"
export OPENSCENE_DATA_ROOT="/absolute/path/to/dataset"
```

`OPENSCENE_DATA_ROOT` owns logs and sensor bundles. `NUPLAN_MAPS_ROOT` owns
maps and is not interchangeable with the dataset root. `NAVSIM_EXP_ROOT` owns
experiment outputs and metric cache; it is not a sensor or log directory.
`NAVSIM_DEVKIT_ROOT` identifies the installed project workspace for launcher
conventions, but validation does not require reading project files.

Use the value `nuplan-maps-v1.0` for `NUPLAN_MAP_VERSION` with this NAVSIM v2
release. The map API is coupled to that map version even where a downstream
configuration exposes the environment variable.

## Acceptance signals

- `python --version` prints 3.9 or a compatible newer version.
- The three import commands succeed, including `nuplan` before `navsim`.
- `python -m pip check` returns successfully with no conflict lines.
- `validate_workspace.py --split mini` or the intended split prints
  `VALIDATION PASSED`.

Do not treat a successful `import navsim` as proof that maps, logs, camera
blobs, LiDAR blobs, synthetic pickles, or metric cache are present.
