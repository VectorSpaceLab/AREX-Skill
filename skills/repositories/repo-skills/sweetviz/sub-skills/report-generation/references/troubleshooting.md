# Sweetviz report-generation troubleshooting

Use this reference for single-DataFrame `analyze()` plus `show_html()` / `show_notebook()` failures. Route broader install/import/package-data issues to the root troubleshooting reference if present.

## `analyze()` rejects `verbosity`

Symptom:

```text
TypeError: analyze() got an unexpected keyword argument 'verbosity'
```

Cause: the verified public `sweetviz.analyze()` signature is:

```text
analyze(source, target_feat=None, feat_cfg=None, pairwise_analysis='auto')
```

It does not accept `verbosity`. `DataframeReport.__init__` owns `verbosity`, and `config_parser` can set defaults.

Fix options:

```python
import sweetviz as sv

sv.config_parser["General"]["default_verbosity"] = "off"
report = sv.analyze(df, pairwise_analysis="off")
```

or, only when direct constructor use is acceptable:

```python
report = sv.DataframeReport(df, pairwise_analysis="off", verbosity="off")
```

For config-file overrides, route to `../configuration-and-data-handling/`.

## Target column not found

Typical message:

```text
Feature 'target_name' was specified as TARGET, but is NOT FOUND in the dataframe
```

Checks:

- Verify exact column spelling and case.
- Verify the target was not skipped by `FeatureConfig(skip=...)`.
- If the feature is literally named `index`, Sweetviz normalizes that name to `df_index`; route to input/config handling before report generation.
- Verify duplicate columns have been resolved; duplicate column names are unsupported.

## Target cannot be skipped

Typical message:

```text
"target_name" was also specified as "skip". Target cannot be skipped.
```

Fix: remove the target from `FeatureConfig(skip=...)`, or choose a different target. If the user wants to ignore a target-like column, do not pass it as `target_feat`.

## Target contains missing values

Typical message:

```text
Target feature 'target_name' contains NaN (missing) values.
```

Fix before calling Sweetviz:

```python
df = df[df["target_name"].notna()].copy()
# or fill/impute target values only if statistically valid for the user's task
```

Do not suppress this error; Sweetviz requires targets without missing values.

## Target detected as categorical or unsupported

Typical messages include:

```text
TARGET values can only be of NUMERICAL or BOOLEAN type for now.
CATEGORICAL type was detected; if you meant the target to be NUMERICAL, use a FeatureConfig(force_num=...) object.
```

Common causes:

- A low-cardinality numeric target was inferred as categorical.
- A string target is not boolean-like.
- A mixed-type column caused unsupported inference.

Fixes:

```python
feature_config = sv.FeatureConfig(force_num=["target_name"])
report = sv.analyze(df, target_feat="target_name", feat_cfg=feature_config, pairwise_analysis="off")
```

Only force numeric when the data is truly numeric. For mixed strings/numbers, clean the data first and route to `../configuration-and-data-handling/`.

## Pairwise threshold warning

Typical warning begins:

```text
PAIRWISE CALCULATION LENGTH WARNING
```

Cause: `pairwise_analysis="auto"` found more features than the configured association threshold. Pairwise association work grows roughly with `n_features ** 2`.

Fix: recreate the report with an explicit decision:

```python
# Fast report without association graph
report = sv.analyze(df, pairwise_analysis="off")

# Explicitly accept pairwise cost
report = sv.analyze(df, pairwise_analysis="on")
```

Do not continue by rendering the object returned after the auto-threshold warning; rebuild it with `"on"` or `"off"`.

## No association graph appears

If `pairwise_analysis="off"`, this is expected: pairwise associations and association graphs are skipped. Use `"auto"` below the threshold or `"on"` to generate associations.

## HTML report does not open a browser

Browser behavior is optional and environment-dependent.

- `show_html(..., open_browser=True)` saves the file and then asks the local system browser to open it.
- In notebooks, containers, CI, SSH sessions, and remote agents, the browser may not open even though the file was saved.
- Prefer `show_html(..., open_browser=False)` and report the saved path to the user.

Validate the file instead of relying on browser launch:

```python
path = Path("report.html")
assert path.exists() and path.stat().st_size > 1000
```

## HTML file is missing or unexpectedly small

Checks:

- Confirm the parent directory exists and is writable.
- Confirm the process has permission to write the output path.
- Confirm `show_html()` completed without an exception.
- Validate that the file contains `"<html"` and `"sweetviz"`.
- Avoid writing into package or skill runtime directories during user workflows; use a task output directory chosen by the user.

## Invalid layout or scale

Typical layout message:

```text
'layout' parameter must be either 'widescreen' or 'vertical'
```

Fix: pass only `layout="widescreen"` or `layout="vertical"`. Use `scale=None` for defaults or a positive finite float such as `0.85`.

## Notebook/IPython issues

Symptoms:

- `show_notebook()` fails outside a notebook/IPython process.
- The iframe displays but optional file output is not what the user expected.

Guidance:

- Use `show_notebook()` for live notebook embedding only.
- Use `show_html(open_browser=False)` for deterministic HTML file creation outside notebooks.
- If using `show_notebook(filepath=...)`, remember that `file_layout` and `file_scale` affect only the optional file output.

## Comet logging messages

Typical messages:

```text
ERROR: comet_ml is installed, but not configured properly ... HTML reports will not be uploaded.
comet_ml.log_html(): comet_ml is not installed or otherwise ready for logging.
```

Cause: Comet logging is optional and requires the external `comet_ml` package plus configured credentials/service.

Guidance:

- Do not install, configure, or verify Comet unless the user explicitly asks and provides a credentialed environment.
- Local `show_html(open_browser=False)` reports do not require Comet.
- If Comet is installed in an environment where network logging is not desired, run smoke checks in an environment without Comet or disable Sweetviz auto-Comet behavior in the check script.

## Font and glyph warnings

Matplotlib can emit font-family, font-weight, or missing-glyph warnings while Sweetviz still creates a valid report. Validate the HTML output before treating font warnings as fatal.

For CJK/Asian character glyph warnings, enable the Sweetviz CJK font setting through configuration before report creation, or route to `../configuration-and-data-handling/` for config override guidance.
