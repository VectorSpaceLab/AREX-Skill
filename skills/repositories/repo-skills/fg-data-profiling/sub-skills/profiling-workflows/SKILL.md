---
name: profiling-workflows
description: "Guides core fg-data-profiling ProfileReport workflows for pandas
  DataFrames, exports, time-series, type schemas, and report smoke checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Profiling Workflows

Use this sub-skill when the user wants to create, inspect, or export an
fg-data-profiling report with the Python API. This covers the current public
import `data_profiling`, `ProfileReport`, and the pandas `df.profile_report()`
convenience method.

## Read first

- Read [references/api-reference.md](references/api-reference.md) for verified
  signatures, output methods, and summary accessors.
- Read [references/workflows.md](references/workflows.md) for task-oriented
  recipes: minimal EDA, full/explorative reports, time-series, type schemas,
  notebook display, and large-dataset sampling.
- Read [references/data-formats.md](references/data-formats.md) when the user is
  starting from files, pandas readers, or DataFrame shape constraints.
- Read [references/troubleshooting.md](references/troubleshooting.md) for empty
  DataFrames, `sortby`, `minimal`/`config_file`, deprecated imports, and widget
  display failures.
- Run [scripts/profile_dataframe_smoke.py](scripts/profile_dataframe_smoke.py)
  when you need a safe no-network API smoke test that writes a tiny HTML/JSON
  report.

## Core API pattern

```python
import pandas as pd
from data_profiling import ProfileReport

df = pd.DataFrame({"amount": [1.0, 2.5, 3.0], "segment": ["a", "b", "b"]})
profile = ProfileReport(df, title="Dataset profile", minimal=True, progress_bar=False)
profile.to_file("profile.html")
```

If the user already has a pandas DataFrame and has imported `data_profiling`,
the package also registers:

```python
profile = df.profile_report(title="Dataset profile", minimal=True)
```

Prefer `minimal=True` or a sampled DataFrame for first-pass profiling of large
or unfamiliar data. Move performance tuning and report-section controls to
[../configuration-and-output/SKILL.md](../configuration-and-output/SKILL.md)
when the user asks for exact settings.

## Choose the right mode

| User intent | Recommended start |
| --- | --- |
| Quick EDA report for a pandas DataFrame | `ProfileReport(df, minimal=True)` then `to_file("report.html")` |
| Full exploratory report with URL/file/image/text detection | `ProfileReport(df, explorative=True)` and review optional dependencies |
| Time-series EDA | `ProfileReport(df, tsmode=True, sortby="time_column")` if chronological order is a column |
| Known semantic column types | Pass `type_schema={"col": "categorical"}` or a time-series type schema |
| JSON profile values for automation | `json.loads(profile.to_json())` or `profile.get_description()` |
| Sensitive dataset | Route to [../comparison-and-quality/SKILL.md](../comparison-and-quality/SKILL.md) before exposing samples/duplicates |
| Spark DataFrame | Route to [../integrations-and-backends/SKILL.md](../integrations-and-backends/SKILL.md) first |

## Important boundaries

- This sub-skill is API-first. For shell commands, read
  [../cli-and-automation/SKILL.md](../cli-and-automation/SKILL.md).
- For YAML files, environment variables, HTML assets, cache invalidation, and
  serialization, read
  [../configuration-and-output/SKILL.md](../configuration-and-output/SKILL.md).
- For report comparison, privacy redaction, custom samples, metadata, and
  Great Expectations caveats, read
  [../comparison-and-quality/SKILL.md](../comparison-and-quality/SKILL.md).
- For Spark, notebooks, Bytewax, dashboards, and optional dependency readiness,
  read [../integrations-and-backends/SKILL.md](../integrations-and-backends/SKILL.md).

## Safety and validation

- Start with tiny local fixtures before profiling private, very large, or
  expensive datasets.
- Do not rely on the original repository's examples at runtime; use the bundled
  smoke script or adapt the API snippets in this sub-skill.
- If a report has already rendered and the configuration changes, either create
  a fresh `ProfileReport` or use cache invalidation from the configuration
  sub-skill.
- Treat notebook widget rendering as optional; HTML export is the most portable
  output for sharing.
