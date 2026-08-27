---
name: styling-annotations
description: "Customize Chartify labels, legends, axes, callouts, palettes,
  style settings, options, and trusted YAML configuration."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Styling and Annotations

Use this sub-skill when a task asks to polish or configure a Chartify chart: titles, subtitles, source labels, legend placement, axis labels/ranges/ticks, categorical factor order, callout lines/boxes/text, color palettes, accent colors, style settings, or Chartify YAML configuration.

Route data reshaping, plot-method selection, chart-type selection, second-axis plotting, radar plotting, and save/show basics to sibling [`basic-charting`](../basic-charting/SKILL.md). Use the root skill for installation/import checks and cross-cutting browser export caveats.

## Read/Run These Files

- Read [references/api-reference.md](references/api-reference.md) when you need verified method signatures for labels, legends, axes, callouts, palettes, options, colors, or style settings.
- Read [references/workflows.md](references/workflows.md) for copyable patterns that customize labels, axes, legends, callouts, and palettes on a chart object.
- Read [references/configuration.md](references/configuration.md) before creating or loading Chartify option, style, color, or palette YAML files.
- Read [references/troubleshooting.md](references/troubleshooting.md) when a palette name is invalid, a config directory is ignored, axis labels/ticks do not appear as expected, callouts land in the wrong place, or style settings do not apply.
- Run [scripts/check_chartify_style_config.py](scripts/check_chartify_style_config.py) to inspect a Chartify install, print option keys, verify palette lookups, or write a small trusted sample config directory.

## Quick Route Map

| Task | Start here |
| --- | --- |
| Set title, subtitle, source label, or legend location | [references/workflows.md](references/workflows.md#1-add-labels-and-legend-placement) |
| Set numeric/date ranges, tick values, tick formats, or factor order | [references/workflows.md](references/workflows.md#2-format-axes-and-factor-order) |
| Add vertical/horizontal reference lines, segments, shaded boxes, or text labels | [references/workflows.md](references/workflows.md#3-add-callouts) |
| Select categorical/sequential/diverging/accent palettes | [references/workflows.md](references/workflows.md#4-choose-palettes-and-apply-config) |
| Create custom colors or palettes | [references/api-reference.md](references/api-reference.md#colors-and-palettes) |
| Persist defaults through `CHARTIFY_CONFIG_DIR` | [references/configuration.md](references/configuration.md) |
| Diagnose style/config issues | [references/troubleshooting.md](references/troubleshooting.md) and [scripts/check_chartify_style_config.py](scripts/check_chartify_style_config.py) |

## Core Workflow

1. Build or receive a `chartify.Chart`/`chartify.RadarChart` object from [`basic-charting`](../basic-charting/SKILL.md).
2. Apply labels first (`set_title`, `set_subtitle`, `set_source_label`) so the chart communicates the takeaway before visual polish.
3. Choose axis controls that match the chart orientation and axis type. Categorical charts use factor order methods; numeric and datetime charts use range/tick methods.
4. Choose the palette type before plotting when color assignment should affect glyph creation. Use accent palettes when a few categories should stand out and all other categories should use a default color.
5. Add callouts after plotting so coordinates are meaningful in the rendered chart. For datetime axes, pass pandas timestamps or parseable datetime strings.
6. Validate by checking `ch.figure` properties, `ch.data`, or a safe HTML save; avoid relying on notebook display as the only proof.

## Decision Points

- Use `style.set_color_palette('categorical', ...)` for unordered groups; use `sequential` or `diverging` only when values have meaningful order.
- Use `accent` palettes with `accent_values` when one or more groups should be highlighted and the rest should fall back to `style.color_palette_accent_default_color`.
- Use `set_xaxis_factors`/`set_yaxis_factors` for categorical axis ordering; use `set_xaxis_range`/`set_yaxis_range` for numeric or datetime axes.
- Use list tick orientations only for grouped categorical axes; each level can have a different orientation.
- Treat Chartify YAML config as trusted local configuration. Do not load YAML from untrusted users because some config paths use unsafe YAML loading.

## Expected Outputs

A successful styling/annotation task usually returns code that mutates and returns a Chartify chart object, plus a validation note such as the updated figure title, axis range/factors, selected palette behavior, or an HTML save result. When a task asks for reusable defaults, provide a config-directory recipe from [references/configuration.md](references/configuration.md) and call out the trusted-file requirement.
