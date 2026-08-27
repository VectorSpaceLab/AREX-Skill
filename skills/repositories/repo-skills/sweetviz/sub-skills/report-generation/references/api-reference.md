# Sweetviz report-generation API reference

Verified package identity for this skill: distribution/import name `sweetviz`, version `2.3.3`. The package exposes Python APIs only; no console entry points are required for report generation.

Base runtime dependencies include pandas, numpy, matplotlib, scipy, jinja2, tqdm, and importlib_resources. Optional Comet logging requires a separate `comet_ml` installation plus a configured account/API key.

## Public single-report constructor

```python
sweetviz.analyze(
    source,
    target_feat=None,
    feat_cfg=None,
    pairwise_analysis="auto",
)
```

Installed signature:

```text
(source: Union[pandas.DataFrame, Tuple[pandas.DataFrame, str]], target_feat: str = None, feat_cfg: sweetviz.feature_config.FeatureConfig = None, pairwise_analysis: str = 'auto')
```

Parameter notes:

- `source`: a pandas `DataFrame`, `[df, "Display name"]`, or `(df, "Display name")`. A plain DataFrame is displayed with the default name `DataFrame`.
- `target_feat`: optional column name to analyze as target. It must pass the target constraints below.
- `feat_cfg`: optional `sweetviz.FeatureConfig` for skipping or forcing feature types. Detailed forcing and config behavior belongs in `../configuration-and-data-handling/`.
- `pairwise_analysis`: one of `"on"`, `"auto"`, or `"off"`. Invalid values raise `ValueError`.

Return value: a `sweetviz.DataframeReport` object, except that a wide DataFrame with `pairwise_analysis="auto"` can print a threshold warning and return before the object is fully useful for rendering. Recreate the report with `"on"` or `"off"` in that case.

## DataframeReport constructor and verbosity

`DataframeReport` is public and owns the `verbosity` argument:

```text
DataframeReport(source, target_feature_name=None, compare=None, pairwise_analysis='auto', fc=None, verbosity='default')
```

Do not claim or assume that `sweetviz.analyze()` accepts `verbosity`; that keyword is invalid for the public `analyze()` function in this installed API.

If verbosity must be controlled, use one of these routes:

```python
# Preferred for most users: set the default before constructing reports.
sv.config_parser["General"]["default_verbosity"] = "off"
report = sv.analyze(df, pairwise_analysis="off")

# Direct constructor route when the task explicitly accepts it.
report = sv.DataframeReport(df, pairwise_analysis="off", verbosity="off")
```

For durable config-file override guidance, route to `../configuration-and-data-handling/`.

## HTML rendering

Installed signature:

```text
DataframeReport.show_html(filepath='SWEETVIZ_REPORT.html', open_browser=True, layout='widescreen', scale=None)
```

Parameter notes:

- `filepath`: output HTML path. The method writes UTF-8 HTML.
- `open_browser`: if `True`, Sweetviz calls the local web browser after saving. Set `False` for agents, CI, notebooks, and remote servers unless the user explicitly wants a browser.
- `layout`: `"widescreen"` or `"vertical"`. Other values raise `ValueError`.
- `scale`: `None` uses configured/default scale; otherwise a float used for report scaling.

Validation after render:

```python
from pathlib import Path

path = Path("SWEETVIZ_REPORT.html")
assert path.exists()
assert path.stat().st_size > 1000
html = path.read_text(encoding="utf-8", errors="ignore").lower()
assert "<html" in html and "sweetviz" in html
```

## Notebook rendering

Installed signature:

```text
DataframeReport.show_notebook(w=None, h=None, scale=None, layout=None, filepath=None, file_layout=None, file_scale=None)
```

Parameter notes:

- `w`: iframe width, such as `"100%"` or a pixel value.
- `h`: iframe height, such as `700`, or `"Full"` for the full report height.
- `scale`: report scale inside the notebook iframe.
- `layout`: `"widescreen"` or `"vertical"`; `None` uses configured notebook defaults.
- `filepath`: optional HTML file output in addition to notebook display.
- `file_layout` and `file_scale`: layout/scale for optional file output only.

Operational notes:

- `show_notebook()` imports IPython display helpers and displays an iframe. It is not a replacement for no-browser file output in plain Python.
- If the user only needs an HTML file, use `show_html(open_browser=False)`.

## Comet logging APIs

Installed signature:

```text
DataframeReport.log_comet(experiment)
```

Behavior:

- `show_html()` and `show_notebook()` instantiate Sweetviz's Comet logger after generating the report. If `comet_ml` is installed and configured, Sweetviz attempts to auto-log the generated HTML.
- `log_comet(experiment)` explicitly logs the report HTML to an existing experiment object.
- If `comet_ml` is missing or not configured, Sweetviz prints a message and ordinary local report generation can still succeed.

Treat Comet as optional and credentialed. Do not verify it in default smoke tests and do not embed credentials in examples.

## Target constraints

A target feature used with `target_feat=...` must satisfy all of the following:

1. The column exists in the source DataFrame after any Sweetviz normalization.
2. It is not listed in `FeatureConfig(skip=...)`.
3. It has no missing/NaN values.
4. Its detected or forced Sweetviz type is boolean or numeric.

Important implication: numeric columns with no more than the configured low-cardinality threshold default to categorical unless forced/configured. If such a column is intended to be a numeric target, use `FeatureConfig(force_num=[target_name])` and read `../configuration-and-data-handling/`.

## Pairwise association behavior

Allowed values: `"on"`, `"auto"`, `"off"`.

- `"off"`: skips pairwise associations and association graphs; fastest and safest for deterministic smoke reports.
- `"auto"`: uses the configured `Processing.association_auto_threshold` to decide whether a wide DataFrame is too expensive. The default threshold is 200 features. Above the threshold Sweetviz warns and returns early; recreate the report with `"on"` or `"off"`.
- `"on"`: computes pairwise associations regardless of width; cost grows roughly with the square of the number of features.

## Related public APIs routed elsewhere

- `sweetviz.compare(source, compare, target_feat=None, feat_cfg=None, pairwise_analysis='auto')` and `sweetviz.compare_intra(...)` are comparison workflows; route to `../dataset-comparison/`.
- `sweetviz.FeatureConfig(skip=None, force_cat=None, force_text=None, force_num=None)` is often needed by report-generation tasks but detailed behavior belongs in `../configuration-and-data-handling/`.
