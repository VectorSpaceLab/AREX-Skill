# Repository Provenance

## Source snapshot

- Project: Ultralytics YOLOv5
- Canonical skill id: `yolov5`
- Source remote: `https://github.com/ultralytics/yolov5.git`
- Branch: `master`
- Commit: `20d1d78a08277e365d57bfa3a2cce752772d9e59`
- Exact tag: none detected at the inspected commit
- Package metadata version: `7.0.0` from `pyproject.toml`
- Python requirement: `>=3.8`
- License: AGPL-3.0

## Working tree state

The source tree was clean before generated skill artifacts were written. After generation, `skills/` contains the new runtime skill and review artifacts and is not part of upstream YOLOv5 source evidence.

## Runtime and inspection baseline

YOLOv5 is documented and verified here as a clone-run repository rather than as a conventional installed distribution. The repository metadata advertises a Python project named `YOLOv5`, but editable installation of the inspected checkout is not relied on by this skill. Public runtime guidance therefore uses clone-run script names and module imports rather than an installed `yolov5` package import.

Private inspection verified these high-level facts without copying private paths into runtime content:

- Base dependencies from `requirements.txt` are enough for core module import and CLI parser checks when PyTorch is installed.
- A CUDA-capable PyTorch environment can also run CPU parser/import checks.
- ONNX, Flask, and pytest were added only for selected export, serving, and deferred native verification surfaces.
- Optional export backends beyond ONNX, logging integrations, Triton, Docker image builds, and large dataset/model downloads were not installed or executed during skill construction.

## Evidence paths

The generated skill was distilled from these relative source paths:

- `README.md`
- `pyproject.toml`
- `requirements.txt`
- `hubconf.py`
- `detect.py`
- `train.py`
- `val.py`
- `export.py`
- `benchmarks.py`
- `models/`
- `models/segment/`
- `segment/`
- `classify/`
- `utils/`
- `utils/segment/`
- `utils/flask_rest_api/`
- `data/*.yaml`
- `data/hyps/*.yaml`
- `data/scripts/*.sh`
- `tests/test_invariant_common.py`
- `tests/test_invariant_export.py`
- `tests/test_flask_rest_api.py`
- `.github/workflows/ci-testing.yml`
- `AGENTS.md`
- `CONTRIBUTING.md`

## Refresh guidance

Refresh this skill if any of these change materially:

- Script parser flags or defaults in `detect.py`, `train.py`, `val.py`, `segment/*.py`, `classify/*.py`, `export.py`, or `benchmarks.py`.
- Public PyTorch Hub signatures or model-loading behavior in `hubconf.py`.
- Model YAML families, checkpoint naming, dataset YAML schema, or task-specific data formats.
- Optional dependency requirements for export formats, Flask serving, logging integrations, or accelerator runtimes.
- Security and validation behavior covered by the native tests, especially URL validation, export subprocess handling, TensorRT error reporting, mask scaling, and Flask upload validation.
