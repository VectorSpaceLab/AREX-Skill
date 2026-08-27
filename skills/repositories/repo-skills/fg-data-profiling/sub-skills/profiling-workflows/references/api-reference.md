# ProfileReport API Reference

## When to read

Read this when a user asks for exact API names, parameters, outputs, or summary
access patterns for the core fg-data-profiling Python API.

## Main imports

```python
import data_profiling
from data_profiling import ProfileReport, compare
```

`ydata_profiling` remains as a deprecated compatibility import and emits a
`DeprecationWarning`; prefer `data_profiling` in new code.

## Verified `ProfileReport` constructor shape

The inspected signature is:

```python
ProfileReport(
    df=None,
    minimal=False,
    tsmode=False,
    sortby=None,
    sensitive=False,
    explorative=False,
    sample=None,
    config_file=None,
    lazy=True,
    typeset=None,
    summarizer=None,
    config=None,
    type_schema=None,
    **kwargs,
)
```

Important parameters:

| Parameter | Use |
| --- | --- |
| `df` | A pandas DataFrame, or optional Spark DataFrame when Spark dependencies/runtime are ready. |
| `minimal=True` | Uses the minimal preset and disables expensive report sections. Mutually exclusive with `config_file`. |
| `tsmode=True` | Activates time-series analysis for pandas data. It is not supported for Spark DataFrames. |
| `sortby="column"` | Sorts and indexes pandas data by a chronological column when `tsmode=True`. Missing columns raise pandas `KeyError`. |
| `sensitive=True` | Redacts categorical/text values and should be combined with privacy guidance in the comparison/quality sub-skill. |
| `explorative=True` | Enables an exploratory group with URL/path/file/image handling and deeper categorical/text character analysis. |
| `sample={...}` | Replaces report sample output with a custom sample object; useful for privacy-safe synthetic samples. |
| `config_file="settings.yml"` | Loads a YAML settings file; do not combine with `minimal=True`. |
| `lazy=False` | Forces report computation at construction. Requires a non-empty DataFrame. |
| `config=Settings()` | Supplies a prebuilt settings object. |
| `type_schema={"col": "categorical"}` | Overrides semantic type inference for selected columns. |
| `**kwargs` | Accepts settings fields such as `title`, `html`, `plot`, `samples`, `correlations`, or `missing_diagrams`. |

## Output and inspection methods

| Method/property | Result | Notes |
| --- | --- | --- |
| `profile.to_file(path, silent=True)` | Writes `.html` or `.json` depending on suffix | Unknown suffixes are treated as HTML and warned about. |
| `profile.to_html()` / `profile.html` | Returns HTML string | Uses cached rendered HTML unless invalidated. |
| `profile.to_json()` / `profile.json` | Returns JSON string | JSON contains analysis, table, variables, alerts, missing, sample, duplicates, correlations, package, and scatter keys. |
| `profile.to_notebook_iframe()` | Displays iframe in notebooks | Needs IPython display support. |
| `profile.to_widgets()` | Displays widget UI | Needs notebook/widget dependencies; Colab may warn. |
| `profile.get_description()` | Returns the raw description dataclass | Use for automation and comparison inputs. |
| `profile.get_sample()` | Returns configured samples | Honors custom samples and sample settings. |
| `profile.get_duplicates()` | Returns duplicate rows/counts or `None` | Controlled by duplicate settings. |
| `profile.get_rejected_variables()` | Returns a set of rejected variable names | Based on generated alerts. |
| `profile.invalidate_cache(subset=None)` | Clears cached render/report data | See configuration/output sub-skill for details. |

## Pandas decorator

After importing the package, pandas DataFrames have a convenience method:

```python
report = df.profile_report(title="Quick EDA", minimal=True)
```

This method simply constructs `ProfileReport(df, **kwargs)`.

## Tiny validation snippet

```python
import pandas as pd
from data_profiling import ProfileReport

df = pd.DataFrame({"x": [1, 2, 3], "cat": ["a", "b", "b"]})
profile = ProfileReport(df, minimal=True, progress_bar=False)
assert profile.to_json().lstrip().startswith("{")
assert "html" in profile.to_html().lower()
```

Use the bundled smoke script when you want file-output validation rather than an
inline snippet.
