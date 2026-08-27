---
name: timelapse-and-apps
description: "Create geemap timelapse animations, local GIF/MP4 post-processing,
  and app export/deployment workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# geemap Timelapse and Apps

Use this sub-skill when a task asks for geemap satellite timelapse generation, animated GIF or MP4 post-processing, map-to-app export, or lightweight publication/deployment patterns.

## Start here

1. Confirm geemap, Earth Engine, and optional app dependencies with [../../references/installation-and-auth.md](../../references/installation-and-auth.md).
2. Decide whether the task is local-only or remote Earth Engine:
   - Local-only GIF/MP4 annotation/conversion: use [scripts/gif_tool.py](scripts/gif_tool.py) and [references/workflows.md](references/workflows.md#deterministic-local-gifmp4-workflows).
   - Remote satellite timelapse generation: use [references/workflows.md](references/workflows.md#remote-earth-engine-timelapse-workflows) and the function notes in [references/api-reference.md](references/api-reference.md).
   - Web/app output: use [references/workflows.md](references/workflows.md#web-app-and-publication-workflows).
3. If anything fails, check [references/troubleshooting.md](references/troubleshooting.md) before changing the workflow.

## What this sub-skill owns

- Earth Engine timelapse functions from `geemap.timelapse`: Landsat, Sentinel-2, Sentinel-1, GOES, NAIP, MODIS NDVI/ocean-color, generic ImageCollection timelapse, Dynamic World timeseries, text/progress overlays, fading, and GIF-to-MP4 conversion.
- `geemap.Map.add_landsat_ts_gif` when the user wants to draw/select an ROI on an interactive map and overlay the generated Landsat GIF back onto the map.
- Deterministic local post-processing of an existing GIF: inspect frames, create tiny fixture GIFs, add frame labels/progress bars through geemap, and convert to MP4 when `ffmpeg` is available.
- Map output and app routes: `Map.to_html`, `Map.to_streamlit`, folium `to_gradio`, folium Streamlit bidirectional mode, Voila/ngrok-style notebook serving, Solara/Streamlit/Gradio optional extras, and folium Datapane publishing when the required package and token are present.

## Route elsewhere

- General Earth Engine layer creation, basemaps, widgets, draw controls, inspectors, or map backend selection: [../interactive-earth-engine-maps/SKILL.md](../interactive-earth-engine-maps/SKILL.md).
- Static maps, charts, colorbars/legends outside an animation, cartoee outputs, Plotly/pydeck/kepler/maplibre visualization decisions: [../visualization-and-charts/SKILL.md](../visualization-and-charts/SKILL.md).
- Generic Earth Engine exports, shapefile/GeoJSON/CSV/raster conversion, COG/STAC/OSM data movement, or export task monitoring not tied to a timelapse output: [../conversion-and-io/SKILL.md](../conversion-and-io/SKILL.md).
- ML classifiers, Dynamic World classification analysis beyond animation/time-series display, Gemini/AI dataset discovery, or classifier conversion: [../machine-learning-and-ai/SKILL.md](../machine-learning-and-ai/SKILL.md).

## Operating constraints

- Keep local GIF/MP4 processing separate from remote Earth Engine generation. Local processing should not initialize Earth Engine or require credentials.
- Remote timelapse generation requires an initialized Earth Engine session, network access, a valid ROI, sensible date ranges, and output dimensions small enough for Earth Engine video/thumbnail services.
- Most timelapse functions write a GIF path and may also write an MP4 when `mp4=True`; MP4 conversion requires a system `ffmpeg` binary.
- Large exports are more fragile. Start with a small ROI, `dimensions<=768`, annual or monthly frequency, and a short date span before increasing size or temporal density.
- App routes require optional extras and service tokens depending on target. Treat Streamlit, Gradio, Voila, Solara, Datapane, ngrok, and browser ports as deployment prerequisites, not core geemap computation.
- Do not rely on source notebooks or repository checkout files at runtime; the self-contained references and bundled script in this sub-skill are the supported operating material.
