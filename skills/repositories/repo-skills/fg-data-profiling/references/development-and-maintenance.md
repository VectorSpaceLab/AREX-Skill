# Development and Maintenance Reference

## When to read

Read this only when a user is editing, testing, documenting, or packaging an
fg-data-profiling repository checkout. Package users should normally start from
the workflow sub-skills instead.

## Supported Python and install baseline

The package metadata supports Python `>=3.10,<3.14`. The CI matrix exercises
Python 3.10 through 3.13 for the base tests, and Spark CI uses selected Python
3.10, 3.11, and 3.12 combinations with PySpark 3.5 or 4.0.

For maintainer work, install the package in editable mode with only the extras
needed for the task. Avoid broad extras unless the task really includes docs,
notebooks, Spark, or full test coverage.

```bash
python -m pip install --upgrade pip "setuptools<81" wheel
python -m pip install -e ".[notebook]"
```

Use the public package import after install:

```bash
python - <<'PY'
import data_profiling
from data_profiling import ProfileReport
print(data_profiling.__version__)
print(ProfileReport)
PY
```

## Focused test commands

The repository Makefile divides checks by surface:

```bash
pytest tests/unit/
pytest tests/issues/
pytest --nbval tests/notebooks/
data_profiling -h
```

Spark checks are separate and require Java plus PySpark:

```bash
pytest tests/backends/spark_backend/
data_profiling -h
```

When editing a narrow package area, prefer focused tests first. Examples:

| Edited surface | Focused checks |
| --- | --- |
| CLI parser or file readers | `pytest tests/unit/test_console.py -q` and `data_profiling -h` |
| Settings/config shorthands | `pytest tests/unit/test_config.py tests/unit/test_report_options.py -q` |
| HTML export/assets/themes | `pytest tests/unit/test_html_export.py -q` |
| Report comparison | `pytest tests/unit/test_comparison.py -q` |
| Sensitive/custom samples | `pytest tests/unit/test_sensitive.py tests/unit/test_custom_sample.py -q` |
| Time-series behavior | `pytest tests/unit/test_time_series.py -q` |
| Spark backend | `pytest tests/backends/spark_backend/ -q` after Java/PySpark readiness |

## Packaging notes

The package version is dynamic. In a release/package build, the build process
writes a `VERSION` value into `src/data_profiling/version.py`. In an editable
checkout without `VERSION`, the fallback version may be `0.0.dev0`; use tags and
commit provenance when deciding whether a generated repo skill is stale.

The manifest includes package YAML configs and HTML templates/static resources,
and excludes docs, examples, tests, and development scaffolding from source
distributions. That is why generated skill helpers should not rely on original
examples or docs being installed with the package.

## Documentation maintenance

Docs are built with MkDocs and table-reader plugin content. If editing settings
or public APIs, update both source behavior and the relevant docs tables or
guides. Keep in mind that some docs still use old package names or old extra
names; verify against `pyproject.toml` before copying install instructions.

## Spark maintenance caveats

Spark tests require Java and a local Spark configuration. CI sets local binding
variables such as `SPARK_LOCAL_IP=127.0.0.1` and a safe local temp directory.
If local Spark tests hang or fail to bind, check Java availability, PySpark
version, host binding, and temp directory permissions before changing package
logic.
