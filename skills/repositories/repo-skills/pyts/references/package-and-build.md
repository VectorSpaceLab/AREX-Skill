# Package and Build Metadata

## Purpose

Read this when you need the verified distribution facts for pyts, including the
install surface, build system, dependencies, extras, package data, and the
compatibility note that affected the verified smoke run.

## Verified facts

- Distribution: `pyts`
- Import root: `pyts`
- Version: `0.13.0`
- Source root: `pyts/`
- Build system: `setuptools` through `setup.py` and `setup.cfg`
- `pyproject.toml`: not present in this snapshot
- Public CLI: none declared
- Python support in metadata/docs: `>=3.8`

## Runtime dependencies

- `numpy>=1.22.4`
- `scipy>=1.8.1`
- `scikit-learn>=1.2.0`
- `joblib>=1.1.1`
- `numba>=0.55.2`

## Optional dependency groups

- `linting`: `flake8`
- `tests`: `pytest`, `pytest-cov`
- `docs`: `docutils`, `sphinx==1.8.5`, `alabaster==0.7.12`, `sphinx-gallery`, `numpydoc`, `matplotlib`, `packaging`

## Package data

The wheel/install includes cached toy datasets and dataset metadata under
`pyts/datasets/cached_datasets/` and `pyts/datasets/info/`.

## Install guidance

For a fresh editable install in a verified environment, use:

```bash
python -m pip install -e .
python -m pip install 'scikit-learn<1.6' pytest
```

The second command reflects the verified compatibility pin for the current
snapshot. Keep it in mind if `dtw` starts failing after a dependency upgrade.

## Useful follow-up

- Read `references/troubleshooting.md` for the DTW/scikit-learn compatibility
  note and other cross-cutting failures.
- Run `scripts/pyts_smoke.py --mode core` or one of the sub-skill wrappers
  under `sub-skills/*/scripts/` to confirm the installed package.
