---
name: chartify
description: "Use Spotify Chartify to build tidy pandas/Bokeh charts, route plot
  workflows, customize styling, and diagnose output/configuration issues."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Chartify Repo Skill

Use this skill when a task names Chartify or asks for a Python data-visualization workflow that matches Chartify's surface: tidy pandas `DataFrame` inputs, Bokeh-backed charts, simple chart construction, categorical/numeric/datetime/density plots, radar charts, labels/legends/callouts, color palettes, style defaults, or Chartify-specific save/show troubleshooting.

Chartify is a Python library that makes plotting simpler for data scientists. It provides a small top-level API (`chartify.Chart`, `chartify.RadarChart`, `chartify.color_palettes`, `chartify.options`, and `chartify.examples`) over Bokeh.

## Install and Import Check

```bash
pip install chartify
python - <<'PY'
import chartify
print(chartify.__version__)
ch = chartify.Chart(blank_labels=True)
print(type(ch.plot).__name__, type(ch.axes).__name__)
PY
```

Python support in the source snapshot is `>=3.9,<4`. Runtime dependencies include pandas, Pillow, Selenium, Bokeh, SciPy, IPython/ipykernel, PyYAML, Jinja2, jupyter-bokeh, and Tornado. PNG/SVG export additionally needs a compatible browser and driver; HTML output is the safest portable check.

Run [scripts/check_chartify_runtime.py](scripts/check_chartify_runtime.py) when you need a quick import/API smoke check, optional HTML save check, or browser-driver probe.

## Routing

| User task | Use |
| --- | --- |
| Create line, scatter, area, text, bar, stacked bar, boxplot, interval, lollipop, parallel, heatmap, histogram, KDE, hexbin, radar, or second-y-axis charts | [`sub-skills/basic-charting`](sub-skills/basic-charting/SKILL.md) |
| Decide `x_axis_type`/`y_axis_type`, transform pandas grouped/pivoted data, inspect `ch.data`, or save/show output | [`sub-skills/basic-charting`](sub-skills/basic-charting/SKILL.md) |
| Set title, subtitle, source label, legend, axes, ticks, ranges, factor order, callouts, palettes, style settings, options, or YAML config | [`sub-skills/styling-annotations`](sub-skills/styling-annotations/SKILL.md) |
| Diagnose install/import/Bokeh/Selenium/browser-driver/config issues shared across workflows | [references/troubleshooting.md](references/troubleshooting.md) |
| Check whether this generated skill matches a checkout/version | [references/repo-provenance.md](references/repo-provenance.md) |
| Inspect top-level package object map and dependency facts | [references/api-overview.md](references/api-overview.md) |

## Core Usage Pattern

1. Normalize inputs to a tidy pandas `DataFrame` with every plotted dimension as a named column. Use `reset_index()` after `groupby` and `pd.melt(...)` for pivoted data.
2. Construct `chartify.Chart(...)` with axis types that expose the needed plot method. Use `x_axis_type='datetime'` for datetime x data and `x_axis_type='categorical'` or `y_axis_type='categorical'` for categorical charts.
3. Plot through `ch.plot.<method>(...)` using column names, not Series objects.
4. Apply labels, legends, axes, callouts, and palettes. For advanced styling/configuration, route to [`styling-annotations`](sub-skills/styling-annotations/SKILL.md).
5. Validate with `ch.data`, figure properties, or an HTML save. Use PNG/SVG only when the browser-driver requirement is satisfied.

## Output and Rendering Notes

- `ch.show(format='html')` and `ch.save(filename, format='html')` are the most portable paths.
- `format='png'` and `format='svg'` use Bokeh/Selenium browser export. If Chrome/Chromedriver or another compatible browser driver is missing, document the limitation instead of treating core chart construction as failed.
- Chartify initializes notebook output when running in a Jupyter kernel, but agents should not rely on notebook display as proof. Prefer object assertions or HTML save checks.

## Boundaries

Use this skill for operating Chartify as a library. Do not use it for generic Bokeh-only charting unless the user explicitly wants Chartify. Do not use it for maintaining release infrastructure, docs builds, CI, or repository contribution process unless the user asks to modify the Chartify repository itself; then use general Python repository maintenance guidance plus the provenance file to decide whether the skill is stale.

## Evidence and Refresh

The generated skill is self-contained and distills evidence from the source package, examples, docs, notebooks, and tests at the snapshot recorded in [references/repo-provenance.md](references/repo-provenance.md). If the installed Chartify version, public signatures, or source commit differ materially, refresh the skill before relying on edge-case guidance.
