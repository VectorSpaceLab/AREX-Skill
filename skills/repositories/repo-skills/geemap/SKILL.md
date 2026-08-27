---
name: geemap
description: "Use geemap for Google Earth Engine interactive mapping, geospatial
  conversion, visualization, timelapse, and ML helper workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# geemap

Use this repo skill when the task involves **geemap**, the Python package for interactive geospatial analysis and visualization with Google Earth Engine (GEE). It covers map construction, Earth Engine layers, data conversion/export, charts and cartographic output, timelapse animations, app publication, local ML classifier conversion, and optional AI dataset-search helpers.

## Start here

1. Confirm installation, Python version, Earth Engine credentials, and optional extras with [references/installation-and-auth.md](references/installation-and-auth.md).
2. Run the safe package smoke helper when the user asks you to check an environment: [scripts/check_geemap_env.py](scripts/check_geemap_env.py).
3. Pick the narrowest sub-skill below. If a workflow spans several areas, start with the primary output and follow the cross-links.
4. For repository freshness or refresh decisions, read [references/repo-provenance.md](references/repo-provenance.md).
5. For cross-cutting failures before diving into a workflow-specific page, read [references/troubleshooting.md](references/troubleshooting.md).

## Route map

| User intent | Read |
|---|---|
| Create a `geemap.Map`, choose ipyleaflet vs folium, add Earth Engine layers, basemaps, WMS/XYZ/COG/STAC/local raster layers, drawing tools, inspectors, layer managers, or save/embed an interactive map | [sub-skills/interactive-earth-engine-maps/SKILL.md](sub-skills/interactive-earth-engine-maps/SKILL.md) |
| Convert Earth Engine JavaScript to Python/notebooks, convert local vector/raster formats, export EE Images/FeatureCollections/videos, use COG/STAC/titiler helpers, or diagnose CRS/selectors/export tasks | [sub-skills/conversion-and-io/SKILL.md](sub-skills/conversion-and-io/SKILL.md) |
| Create charts, colorbars, palettes, legends, cartoee/cartopy static maps, Plotly maps, pydeck, kepler.gl, or MapLibre visualizations | [sub-skills/visualization-and-charts/SKILL.md](sub-skills/visualization-and-charts/SKILL.md) |
| Generate Landsat/Sentinel/GOES/NAIP/MODIS/Dynamic World timelapses, annotate GIFs, convert GIF/MP4, publish maps to HTML/Streamlit/Gradio/Voila/Solara-style apps | [sub-skills/timelapse-and-apps/SKILL.md](sub-skills/timelapse-and-apps/SKILL.md) |
| Convert local scikit-learn trees/random forests into Earth Engine classifiers, plan EE classification workflows, or use optional Gemini/AI dataset-discovery helpers | [sub-skills/machine-learning-and-ai/SKILL.md](sub-skills/machine-learning-and-ai/SKILL.md) |

## Minimal setup pattern

```bash
pip install geemap
python - <<'PY'
import geemap
print(geemap.__version__)
Map = geemap.Map(center=[40, -100], zoom=4, ee_initialize=False)
print(type(Map).__name__)
PY
```

Use `ee_initialize=False` for offline map construction or tests that should not contact Earth Engine. For real GEE layers or exports, authenticate and initialize Earth Engine first; see [installation and auth](references/installation-and-auth.md#earth-engine-authentication-and-projects).

## Optional extras decision points

- Base map, conversion, local helper, and many tests use the base package.
- `geemap[backends]` adds pydeck and kepler.gl routes.
- `geemap[raster]`, `geemap[vector]`, and `geemap[sql]` add local raster, GeoPandas/OSM, and PostGIS-style workflows.
- `geemap[apps]` adds app-publication targets.
- `geemap[ai]` adds Gemini/LangChain/Google Cloud AI dataset-search routes.
- Avoid `geemap[all]` unless the user truly needs broad optional coverage; many extras bring compiled geospatial dependencies, services, credentials, or UI packages.

## Safety and execution boundaries

- Do not run Earth Engine exports, notebook corpora, OSM/network downloads, cloud storage jobs, AI service calls, or app deployments unless the user explicitly wants those side effects and has credentials/network available.
- Prefer safe helper checks and dry-run planning scripts first; launch remote tasks only after validating ROI, scale, CRS, selectors, output path, and destination.
- Keep generated answers self-contained. Use this skill tree's references and scripts instead of depending on a repository checkout.
- CUDA/ROCm/MPS are not required for geemap itself; the important runtime gates are Python/Jupyter widgets, Earth Engine authentication, network access, and optional geospatial/service dependencies.
