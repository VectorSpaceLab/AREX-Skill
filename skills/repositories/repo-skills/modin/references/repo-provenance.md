# Repository provenance

This runtime graph was distilled from the public Modin repository.

- `source_repository`: modin-project/modin
- `remote_url`: https://github.com/modin-project/modin.git
- `source_commit`: `7ca200b08597ed6ecfd2db2d08bd322f83c2cec1`
- `branch`: `main`
- `exact_tag`: none observed at the source commit
- `working_tree`: clean tracked state at capture; ignored cache/log artifacts were not used as evidence
- `package_name`: `modin`
- `package_version_at_capture`: `0+untagged.1.g7ca200b`
- `python_requires`: `>=3.9`
- `public_dependency_range`: pandas `>=2.2,<2.4`; NumPy `>=1.22.4`; fsspec `>=2022.11.0`; packaging `>=21.0`; psutil `>=5.8.0`; typing-extensions

## Relative evidence baseline

- `README.md`
- `setup.py`
- `setup.cfg`
- `environment-dev.yml`
- `requirements/requirements-no-engine.yml`
- `requirements-dev.txt`
- `modin/__init__.py`
- `modin/__main__.py`
- `modin/pandas/`
- `modin/config/`
- `modin/distributed/dataframe/pandas/`
- `modin/experimental/pandas/`
- `modin/experimental/batch/`
- `modin/experimental/xgboost/`
- `modin/experimental/spreadsheet/`
- `modin/experimental/sklearn/`
- `modin/experimental/torch/`
- `modin/numpy/`
- `modin/polars/`
- `modin/logging/`
- `docs/getting_started/`
- `docs/supported_apis/`
- `docs/usage_guide/`
- `docs/ecosystem.rst`
- `docs/flow/modin/config.rst`
- `docs/flow/modin/experimental/`
- `docs/flow/modin/distributed/dataframe/pandas.rst`
- `docs/development/architecture.rst`
- `docs/development/contributing.rst`
- `examples/data/`
- `examples/docker/modin-ray/nyc-taxi.py`
- `modin/tests/pandas/`
- `modin/tests/config/`
- `modin/tests/experimental/`
- `modin/tests/numpy/`
- `modin/tests/polars/`
- `modin/tests/interchange/`

## Refresh signal

Refresh this graph when the Modin public package changes engine names, pandas support range, `modin.config` variables, DataFrame/Series backend APIs, experimental module contracts, or optional dependency compatibility. Treat source commit and package version as the baseline; do not infer freshness from any local checkout path.
