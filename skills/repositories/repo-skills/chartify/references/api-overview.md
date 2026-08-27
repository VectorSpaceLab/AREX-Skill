# Chartify API Overview

## Purpose

Read this file for top-level Chartify package facts, dependency/output constraints, and a compact object map. Use sub-skills for detailed plot, styling, and configuration workflows.

## Public Imports

```python
import chartify

chartify.Chart
chartify.RadarChart
chartify.color_palettes
chartify.options
chartify.examples
```

`chartify.__version__` for the source snapshot is `5.0.1`.

## Main Objects

| Object | Use | Detailed route |
| --- | --- | --- |
| `chartify.Chart` | Standard Bokeh-backed chart object. Constructor: `Chart(blank_labels=False, layout='slide_100%', x_axis_type='linear', y_axis_type='linear', second_y_axis=False)`. | [`sub-skills/basic-charting`](../sub-skills/basic-charting/SKILL.md) |
| `chartify.RadarChart` | Radar chart object. Constructor: `RadarChart(blank_labels=False, layout='slide_50%')`. | [`sub-skills/basic-charting`](../sub-skills/basic-charting/SKILL.md#readrun-these-files) |
| `ch.plot` | Axis-dependent plot namespace. Methods change based on `x_axis_type` and `y_axis_type`. | [`basic-charting/references/api-reference.md`](../sub-skills/basic-charting/references/api-reference.md) |
| `ch.axes` | Axis labels, ranges, ticks, formats, factor order, and visibility. | [`styling-annotations/references/api-reference.md`](../sub-skills/styling-annotations/references/api-reference.md) |
| `ch.callout` | Reference lines, segments, shaded boxes, and text callouts. | [`styling-annotations/references/api-reference.md`](../sub-skills/styling-annotations/references/api-reference.md#callout-apis) |
| `ch.style` | Palette selection and lower-level Bokeh style settings. | [`styling-annotations`](../sub-skills/styling-annotations/SKILL.md) |
| `chartify.color_palettes` | Built-in and custom palette registry. | [`styling-annotations/references/api-reference.md`](../sub-skills/styling-annotations/references/api-reference.md#style-and-palette-apis) |
| `chartify.options` | Process-local and config-file-backed defaults. | [`styling-annotations/references/configuration.md`](../sub-skills/styling-annotations/references/configuration.md) |
| `chartify.examples` | Public example functions and sample data generator. | Use as conceptual examples; the generated skill bundles safe smoke equivalents in [`basic-charting/scripts/chartify_smoke_examples.py`](../sub-skills/basic-charting/scripts/chartify_smoke_examples.py). |

## Dependency and Output Facts

- Python requirement from package metadata: `>=3.9,<4`.
- Base runtime dependencies: pandas, Pillow, Selenium, Bokeh, SciPy, ipykernel, IPython, PyYAML, Jinja2, jupyter-bokeh, Tornado, and their transitive dependencies.
- No package CLI entry points are exposed in the source snapshot.
- Core chart construction is CPU-only.
- HTML save/display uses Bokeh HTML and is the safest portable output path.
- PNG/SVG save/display uses Bokeh export through Selenium and requires a browser/driver installed outside Python.
- Jupyter notebooks are supported through IPython/Bokeh notebook output, but generated-agent validation should prefer non-interactive object checks or HTML save.

## Axis-Type Surface at a Glance

| Axis configuration | Plot family |
| --- | --- |
| numeric/log/datetime x with numeric/log y | line, scatter, text, area |
| categorical x or categorical y paired with numeric/log | bar, stacked bar, boxplot, interval, lollipop, parallel, scatter, text, stacked text |
| categorical x and categorical y | heatmap |
| one density axis | histogram, KDE |
| both axes density | hexbin |
| `RadarChart` | radar area, perimeter, radius, text |
| `second_y_axis=True` with numeric/log y | secondary numeric y-axis plot namespace and axis namespace |

## Validation Helpers

- Root import/runtime check: [`../scripts/check_chartify_runtime.py`](../scripts/check_chartify_runtime.py)
- Basic chart examples: [`../sub-skills/basic-charting/scripts/chartify_smoke_examples.py`](../sub-skills/basic-charting/scripts/chartify_smoke_examples.py)
- Style/config check: [`../sub-skills/styling-annotations/scripts/check_chartify_style_config.py`](../sub-skills/styling-annotations/scripts/check_chartify_style_config.py)

Each helper imports the installed `chartify` package and avoids depending on a source checkout.
