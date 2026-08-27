---
name: visualization-and-charts
description: "Use geemap charting, colormap, legend, cartoee static map, Plotly,
  pydeck, kepler.gl, and MapLibre visualization workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# geemap visualization and charts

Use this sub-skill when a task needs geemap visual outputs: bqplot charts from local or Earth Engine data, matplotlib colorbars and palettes, built-in dataset legends, publication-style static cartopy/cartoee maps, or optional Plotly, pydeck, kepler.gl, and MapLibre visualization backends.

For package setup and Earth Engine authentication, use the root setup reference: [installation and auth](../../references/installation-and-auth.md). For cross-cutting package failures, use [root troubleshooting](../../references/troubleshooting.md) first, then this sub-skill's [visualization troubleshooting](references/troubleshooting.md).

## Route boundaries

Use this sub-skill for:

- `geemap.chart`: `DataTable`, `Chart`, `array_values`, feature charts, image/region charts, histograms, and time series charts.
- `geemap.colormaps`, top-level `geemap.create_colorbar`, and `geemap.legends`: palettes, colorbars, built-in legends, and legend table conversion.
- `geemap.cartoee`: cartopy-based static maps with Earth Engine layers, colorbars, gridlines, north arrows, scale bars, legends, and `savefig`.
- `geemap.plot` and `geemap.plotlymap`: Plotly Express charts, Plotly map tiles, heatmaps, GeoDataFrames, and static Plotly export.
- `geemap.deck`, `geemap.kepler`, and `geemap.maplibregl`: optional visualization backends and style/layer validation.

Route elsewhere when the primary task is:

- Interactive ipyleaflet or folium map construction, base map controls, drawing widgets, inspectors, and layer managers: [interactive Earth Engine maps](../interactive-earth-engine-maps/SKILL.md).
- Data conversion, local file ingestion, Earth Engine export/download tasks, COG/STAC tile URL generation as a data I/O problem, or OSM acquisition: [conversion and I/O](../conversion-and-io/SKILL.md).
- Timelapse animations, GIF/MP4 production, and app publication workflows: [timelapse and apps](../timelapse-and-apps/SKILL.md).

## Operating checklist

1. Choose the output target before selecting an API:
   - notebook chart: `geemap.chart.Chart` or `geemap.chart.*` wrappers;
   - local tabular chart: `geemap.plot.*` for Plotly Express;
   - publication static map: `geemap.cartoee`;
   - web/notebook map backend: `plotlymap`, `deck`, `kepler`, or `maplibregl`.
2. Check optional backend availability and missing-extra recovery with [backend options](references/backend-options.md).
3. Validate visual parameters before creating the object: color strings, palette length, `min`/`max` scalar values, opacity range, colorbar orientation, legend label/color lengths, and chart reducer/scale/region requirements.
4. For Earth Engine chart or cartoee workflows, make authentication and network needs explicit. Do not treat a local import as proof that remote EE reductions or thumbnail requests will succeed.
5. For a quick no-credentials smoke check, run the bundled script in [scripts/visualization_smoke.py](scripts/visualization_smoke.py).

## Reference bundle

- [Workflows](references/workflows.md): practical recipes for charts, colorbars, static maps, Plotly maps, pydeck, kepler.gl, and MapLibre.
- [API reference](references/api-reference.md): verified signatures and argument contracts.
- [Backend options](references/backend-options.md): dependency, credential, renderer, and fallback matrix.
- [Troubleshooting](references/troubleshooting.md): chart, colorbar, cartoee, optional backend, and token/style failures.
