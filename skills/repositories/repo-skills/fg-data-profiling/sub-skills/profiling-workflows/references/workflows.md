# Core Profiling Workflows

## When to read

Read this for copyable Python recipes that generate fg-data-profiling reports
without relying on repository examples or network datasets.

## Minimal first-pass EDA

Use this when the user has a pandas DataFrame and wants a shareable report with
low risk of expensive computations.

```python
import pandas as pd
from data_profiling import ProfileReport

df = pd.read_csv("data.csv")
profile = ProfileReport(df, title="Initial data profile", minimal=True, progress_bar=False)
profile.to_file("initial-profile.html")
```

For large datasets, sample first and include a dataset description so readers
know the report is sample-based:

```python
sample = df.sample(frac=0.05, random_state=42)
profile = ProfileReport(
    sample,
    title="Sampled profile",
    minimal=True,
    dataset={"description": "Generated from a reproducible 5% sample of the dataset."},
    progress_bar=False,
)
profile.to_file("sampled-profile.html")
```

## Explorative report

Use `explorative=True` when users want richer text/category/URL/path/file/image
analysis. It enables more analysis surfaces and may require optional data or
packages depending on column types.

```python
profile = ProfileReport(df, title="Explorative profile", explorative=True)
profile.to_file("explorative-profile.html")
```

For privacy-sensitive data, route to the privacy reference before enabling rich
samples or value displays.

## Time-series report

Use the source-verified spelling `tsmode`, not stale `ts_mode` spelling.

```python
profile = ProfileReport(
    df,
    title="Time-series profile",
    tsmode=True,
    sortby="event_time",
    minimal=True,
)
profile.to_file("timeseries-profile.html")
```

If `sortby` is omitted, the report assumes the DataFrame is already ordered. If
the column does not exist, pandas raises `KeyError`. Spark DataFrames do not
support time-series mode in this package.

## Override semantic type inference

Use `type_schema` only for variables whose semantic type is known. Other
variables remain inferred.

```python
type_schema = {
    "customer_segment": "categorical",
    "daily_sales": "timeseries",
}
profile = ProfileReport(df, title="Typed profile", type_schema=type_schema)
```

## Export HTML, JSON, and notebook views

```python
profile = ProfileReport(df, title="Outputs", minimal=True)
profile.to_file("profile.html")       # HTML file
profile.to_file("profile.json")       # JSON file
html_text = profile.to_html()          # HTML string
json_text = profile.to_json()          # JSON string
```

Notebook users can display HTML if widget support is uncertain:

```python
profile.to_notebook_iframe()
```

Use widgets only after installing/activating notebook widget support:

```python
profile.to_widgets()
```

## Access profile values for automation

```python
description = profile.get_description()
raw_json = profile.to_json()
```

The JSON output includes keys such as `analysis`, `table`, `variables`,
`alerts`, `missing`, `sample`, `duplicates`, `correlations`, `package`, and
`scatter`. For comparison and quality-oriented interpretation, route to the
comparison/quality sub-skill.

## Safe bundled smoke test

From this sub-skill directory, run:

```bash
python scripts/profile_dataframe_smoke.py --output-dir /tmp/fg-profile-smoke --json
```

The helper creates tiny in-memory data, writes HTML and JSON output, and checks
that output files exist. It is the preferred runtime replacement for networked
sample scripts.
