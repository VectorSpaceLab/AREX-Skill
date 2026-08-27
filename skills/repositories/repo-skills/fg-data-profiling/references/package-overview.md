# Package Overview

## When to read

Read this for package identity, naming, public APIs, extras, and workflow
boundaries that apply across all fg-data-profiling sub-skills.

## Package identity

- Distribution name: `fg-data-profiling`
- Current import: `data_profiling`
- Deprecated compatibility import: `ydata_profiling` emits a
  `DeprecationWarning` and re-exports the same main objects.
- CLI entry points: `data_profiling` and legacy `pandas_profiling`.
- Primary purpose: generate exploratory data analysis and data-quality profile
  reports from pandas DataFrames and, with optional dependencies, Spark
  DataFrames.

The package is the renamed continuation of the old YData/Pandas Profiling API.
Use the public project capitalization in prose, but use `data_profiling` in
imports and `fg-data-profiling` in package-install commands.

## Primary public APIs

```python
import pandas as pd
from data_profiling import ProfileReport, compare

df = pd.DataFrame({"x": [1, 2, 3], "label": ["a", "b", "b"]})
profile = ProfileReport(df, title="EDA", minimal=True, progress_bar=False)
profile.to_file("eda.html")
summary = profile.get_description()
json_payload = profile.to_json()
```

Important calls exposed by the root package and documented in sub-skills:

- `ProfileReport(...)` builds a lazy report object for pandas or optional Spark
  DataFrames.
- `df.profile_report(...)` is added as a pandas DataFrame convenience method by
  the package import.
- `compare([...])` and `profile_a.compare(profile_b)` merge multiple compatible
  profile summaries into a comparison report.
- `to_file()`, `to_html()`, `to_json()`, `to_widgets()`, and
  `to_notebook_iframe()` render or export reports.
- `get_description()`, `get_sample()`, `get_duplicates()`, and
  `get_rejected_variables()` access computed profile details.

## Optional extras and dependency surfaces

The package metadata exposes these optional groups:

| Extra | Use | Notes |
| --- | --- | --- |
| `notebook` | Jupyter widgets and notebook display | Requires notebook/widget frontend support after installation. |
| `spark` | PySpark profiling backend | Needs PySpark plus a working Java/Spark runtime. Some docs still mention `[pyspark]`; the package metadata uses `[spark]`. |
| `unicode` | Rich Unicode script/block names | Base behavior falls back to Python Unicode categories if the extra is absent. |
| `docs`, `dev`, `test` | Maintainer/docs/test work | Not needed for normal package use. |

Great Expectations is not a declared current extra. Source APIs still include
`to_expectation_suite()`, but the public docs warn that the integration is no
longer supported in current versions and point to older compatible pins.

## Capability boundaries

| Task family | Start here |
| --- | --- |
| Create a pandas EDA/profile report, export HTML/JSON, inspect summaries | `sub-skills/profiling-workflows/` |
| Run `data_profiling` from shell, Airflow, IDE external tools, or scripts | `sub-skills/cli-and-automation/` |
| Tune settings, YAML config, env vars, report sections, assets, serialization | `sub-skills/configuration-and-output/` |
| Compare reports, redact sensitive values, attach metadata, inspect quality | `sub-skills/comparison-and-quality/` |
| Spark/notebook/GE/Bytewax/app embedding/optional dependency readiness | `sub-skills/integrations-and-backends/` |
| Edit or test the package repository itself | `references/development-and-maintenance.md` |

## Verification baseline

The skill was created from a CPU/Pandas-verified package scope. The inspected
runtime successfully imported `data_profiling` and `ydata_profiling`, resolved
distribution metadata, ran both CLI help commands, inspected `ProfileReport`,
`compare`, `Settings`, and `console.parse_args` signatures, and generated HTML,
JSON, and comparison output from a tiny pandas DataFrame.

Optional Spark runtime was not installed or verified because Java was absent in
the creation environment and Spark was not required for the selected CPU scope.
Future agents should run the bundled Spark readiness diagnostic before making
Spark-specific claims for a user's environment.
