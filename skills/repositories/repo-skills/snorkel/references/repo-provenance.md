# Repo provenance

This generated repo skill was distilled from the public Snorkel Python package.

## Source snapshot

- Repository: Snorkel
- Public source URL: `https://github.com/snorkel-team/snorkel/`
- Commit: `45824f9867228c6cb6c9fdc2afd2b7e5bb7fd0b3`
- Branch: `main`
- Exact tag at commit: none detected
- Source working tree state before generated skill files were written: clean
- Package distribution/import name: `snorkel`
- Package version: `0.10.1+dev`
- Python requirement from package metadata: Python `>=3.11`

## Evidence paths used

- `README.md`
- `CONTRIBUTING.md`
- `pyproject.toml`
- `setup.py`
- `setup.cfg`
- `requirements.txt`
- `requirements-pyspark.txt`
- `tox.ini`
- `docs/index.rst`
- `docs/packages.json`
- `docs/packages/analysis.rst`
- `docs/packages/augmentation.rst`
- `docs/packages/classification.rst`
- `docs/packages/labeling.rst`
- `docs/packages/map.rst`
- `docs/packages/preprocess.rst`
- `docs/packages/slicing.rst`
- `docs/packages/utils.rst`
- `snorkel/analysis/`
- `snorkel/augmentation/`
- `snorkel/classification/`
- `snorkel/labeling/`
- `snorkel/map/`
- `snorkel/preprocess/`
- `snorkel/slicing/`
- `snorkel/synthetic/`
- `snorkel/types/`
- `snorkel/utils/`
- `test/analysis/`
- `test/augmentation/`
- `test/classification/`
- `test/labeling/`
- `test/map/`
- `test/slicing/`
- `test/synthetic/`
- `test/utils/`
- `scripts/check_requirements.py`
- `scripts/sync_api_docs.py`

## Refresh guidance

Refresh this skill if the Snorkel package version, public API exports, Python requirement, dependency pins, `docs/packages.json`, or tests around labeling, transforms, classification, slicing, Spark, Dask, or spaCy workflows change.

The generated skill intentionally avoids depending on the original repository checkout. Runtime references and scripts use installed-package imports and bundled guidance only.
