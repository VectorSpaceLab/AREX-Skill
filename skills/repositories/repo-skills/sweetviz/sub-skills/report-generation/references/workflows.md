# Sweetviz single-DataFrame report workflows

These workflows assume an installed `sweetviz` package, pandas input already loaded as a `DataFrame`, and a task that profiles one dataset rather than comparing two datasets.

## 1. Minimal no-browser HTML report

Use this path for scripts, CI, remote agents, and notebooks where opening a browser is undesirable.

```python
from pathlib import Path
import sweetviz as sv

# df is an existing pandas DataFrame.
report = sv.analyze([df, "Analysis dataset"], pairwise_analysis="off")
report.show_html(
    filepath="sweetviz_report.html",
    open_browser=False,
    layout="vertical",      # or "widescreen"
    scale=0.9,              # or None for configured/default scale
)

output = Path("sweetviz_report.html")
assert output.exists(), "Sweetviz did not create the HTML report"
assert output.stat().st_size > 1000, "Sweetviz HTML report is unexpectedly small"
html = output.read_text(encoding="utf-8", errors="ignore").lower()
assert "<html" in html and "sweetviz" in html, "Output does not look like a Sweetviz HTML report"
```

Decision points:

- Pass a plain `DataFrame` for the default report name, or `[df, "Human name"]` / `(df, "Human name")` to show a meaningful dataset label in the report.
- Prefer `pairwise_analysis="off"` when the user only needs fast profiling or deterministic smoke checks.
- Use `layout="vertical"` for narrow displays and `layout="widescreen"` when horizontal detail panes are desired.
- Use `open_browser=False` unless the user explicitly wants a local browser launch.

## 2. Target-aware single-DataFrame report

Sweetviz target analysis highlights relationships between one target column and the other features.

Preflight the target before creating the report:

```python
target = "converted"
assert target in df.columns, "target column is missing"
assert not df[target].isna().any(), "Sweetviz targets cannot contain missing values"
```

Then create and save the report:

```python
import sweetviz as sv

report = sv.analyze(
    [df, "Conversion dataset"],
    target_feat="converted",
    pairwise_analysis="off",
)
report.show_html("conversion_sweetviz.html", open_browser=False)
```

Target constraints to enforce or route for cleanup:

- The target name must exist in the source DataFrame, with matching case.
- The target cannot also be listed in `FeatureConfig(skip=...)`.
- The target cannot contain `NaN`/missing values.
- The target must be boolean or numeric after Sweetviz type detection. Low-cardinality numeric columns can be inferred as categorical by default; route to `../configuration-and-data-handling/` and use `FeatureConfig(force_num=[target])` if the target is truly numeric.
- Duplicate column names and mixed inferred data types are unsupported; route input cleanup to `../configuration-and-data-handling/`.

## 3. Low-cardinality numeric feature with no-browser vertical output

This common workflow spans report generation plus feature configuration. Numeric columns with no more than the configured low-cardinality threshold default to categorical unless forced.

```python
import sweetviz as sv

feature_config = sv.FeatureConfig(force_num=["rating"])
report = sv.analyze(
    [df, "Ratings"],
    target_feat="success",          # optional; must still pass target checks
    feat_cfg=feature_config,
    pairwise_analysis="off",
)
report.show_html(
    "ratings_vertical.html",
    open_browser=False,
    layout="vertical",
    scale=0.85,
)
```

If the task asks for detailed type-forcing strategy, config files, or preflight validation, read `../configuration-and-data-handling/` before finalizing the report code.

## 4. Pairwise analysis decision

`pairwise_analysis` controls Sweetviz association/correlation calculations and graphs:

| Value | Use when | Behavior |
| --- | --- | --- |
| `"off"` | Fast reports, smoke tests, many columns, or when associations are not needed. | Skips pairwise association calculation and association graphs. |
| `"auto"` | Moderate-width data where default behavior is acceptable. | Runs below the configured association threshold; above it, prints a length warning and returns early, so choose `"on"` or `"off"` and rerun. |
| `"on"` | The user explicitly wants association graphs and accepts quadratic cost. | Forces pairwise association calculation regardless of width. |

When a user reports a pairwise threshold warning, do not try to render the returned partial object. Ask them to choose `pairwise_analysis="off"` or `pairwise_analysis="on"`, then recreate the report.

## 5. Notebook embedding

Use `show_notebook()` only inside an IPython/Jupyter-style environment:

```python
report = sv.analyze(df, pairwise_analysis="off")
report.show_notebook(
    w="100%",
    h=700,
    layout="vertical",
    scale=0.9,
)
```

Important notebook notes:

- `show_notebook()` imports IPython display helpers and displays an iframe before optional file output. In a plain Python process, prefer `show_html(open_browser=False)`.
- `filepath=...` on `show_notebook()` writes an optional HTML file after the notebook display path is initialized.
- `file_layout` and `file_scale` affect only the optional file output, not the embedded iframe.

## 6. Optional Comet logging

Sweetviz can log reports to Comet in two ways, but both require external setup:

```python
# Auto behavior: when comet_ml is installed and configured, show_html() and
# show_notebook() attempt to log the generated report.
report.show_html("report.html", open_browser=False)

# Explicit behavior: pass an already-created Comet experiment object.
report.log_comet(experiment)
```

Treat Comet as optional and credentialed:

- Do not require `comet_ml` for ordinary Sweetviz report generation.
- Do not place API keys or workspace credentials in scripts or runtime docs.
- In offline, CI, or agent contexts, skip Comet verification unless the user explicitly provides a configured credentialed environment.

## 7. Bundled smoke script

From this sub-skill directory, run a deterministic no-browser smoke report:

```bash
python scripts/sweetviz_smoke_report.py \
  --output smoke_report.html \
  --layout vertical \
  --scale 0.85 \
  --pairwise-analysis off \
  --force-num-low-cardinality
```

To demonstrate a low-cardinality numeric target that must be forced numeric:

```bash
python scripts/sweetviz_smoke_report.py \
  --output rating_target_report.html \
  --layout vertical \
  --pairwise-analysis off \
  --target rating \
  --force-num-low-cardinality
```

The script prints the output path and byte size after validating that the generated file looks like a Sweetviz HTML report. It never opens a browser and disables optional auto-Comet logging for the smoke run.
