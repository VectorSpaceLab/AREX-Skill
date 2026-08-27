# Installation

## Purpose

Read this before installing Darkflow or preparing a reusable inspection environment. The repo is a legacy TensorFlow 1.x package, so the working install path is narrower than a modern Python project.

## Verified install shape

The environment that successfully imported and inspected Darkflow used:

- Python 3.6
- `tensorflow==1.4.1`
- `opencv-python`
- `numpy`
- `requests`
- `pytest`
- `pytest-cov`
- `Cython<3`

The exact wheel versions can drift, but the important compatibility rule is that the editable install must use a Cython 0.29.x release or another pre-3.0 release. Cython 3 failed to build the bundled extensions.

## Recommended install order

1. Create or select a Python 3.6 environment.
2. Install the build-time and runtime dependencies.
3. Install the package in editable mode.
4. Run the smoke checks.

A practical sequence is:

```bash
python -m pip install 'Cython<3'
python -m pip install tensorflow==1.4.1 opencv-python requests pytest pytest-cov
python -m pip install -e .
python -m pip check
python scripts/check_install.py
flow --help
python scripts/flow.py --help
```

## Notes

- If `pip install -e .` fails with a Cython compile error mentioning `nms.pxd`, reinstall with `Cython<3` and retry.
- TensorFlow 1.4.1 emits noisy warnings on import in the verified environment. They are expected and did not block the package import or CLI help check.
- A CPU-only TensorFlow install is enough for skill drafting and for the help / API inspection checks in this repository.
- GPU acceleration is documented by the project, but a compatible historical GPU stack was not prepared for this inspection.

## What to avoid

- Do not start from a modern TensorFlow 2.x environment and assume the legacy package will behave the same.
- Do not treat the repo's editable install as healthy until `pip check`, a `darkflow` import, and `flow --help` all succeed.
- Do not rely on `Cython==3.x` for this repository.
