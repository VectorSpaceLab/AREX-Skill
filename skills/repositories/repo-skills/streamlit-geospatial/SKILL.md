---
name: streamlit-geospatial
description: "Guides researchers through the streamlit-geospatial multipage
  application, including Streamlit composition, Leafmap/Folium maps, remote
  Earth Engine workflows, and data-backed geospatial dashboards."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# streamlit-geospatial

Use this repo skill when a task asks to build, adapt, troubleshoot, or deploy a
Streamlit geospatial application using the workflow patterns demonstrated by
`streamlit-geospatial`. It is a recipe and routing graph, not a requirement to
keep the original checkout available.

## Route the request

- **Interactive maps**: basemaps, XYZ/QMS search, split maps, heatmaps, marker
  clusters, WMS, COG/raster views, vector uploads, or Folium/Kepler/PyDeck map
  rendering → [interactive-maps](sub-skills/interactive-maps/SKILL.md).
- **Remote geospatial data**: Earth Engine catalog/NLCD, Dynamic World or
  ESA/ESRI land cover, Microsoft building footprints, or Landsat/Sentinel/GOES/
  MODIS/NAIP timelapses → [remote-geospatial-data](sub-skills/remote-geospatial-data/SKILL.md).
- **Dashboards and app shell**: multipage Streamlit structure, U.S. housing
  metrics, PyDeck choropleths, historical Ordnance Survey comparisons, or
  Streamlit deployment → [streamlit-dashboards](sub-skills/streamlit-dashboards/SKILL.md).
- **Cross-cutting install or deployment failure**: read
  [installation and deployment](references/installation-and-deployment.md),
  then [troubleshooting](references/troubleshooting.md).

When a request combines routes, validate local inputs first, then cross the
external Earth Engine or remote-data boundary only after the caller explicitly
provides credentials/network access. Keep each sub-skill's ownership intact.

## Minimum environment

This repository is a Streamlit application rather than an installable Python
distribution. Use Python 3.11 as the conservative inspection/runtime choice,
install the documented Python requirements, and provide the system geospatial
libraries and media tools listed in `packages.txt` when deploying. A typical
runtime install is:

```bash
python -m pip install -r requirements.txt
```

The repository uses `geemap.foliumap` and `geemap.foliumap.Map`. Set the backend
selector before importing that module:

```bash
export USE_FOLIUM=1
python -c "import streamlit, leafmap, geemap, geopandas; print('imports ok')"
```

Run [the environment checker](scripts/check_environment.py) for a deterministic
import/version preflight; it does not start Streamlit, authenticate Earth
Engine, fetch tiles, or download data. Read the installation reference before
using the deployment files because the original setup recipe writes a user
Streamlit config and assumes host-level package installation.

## App composition

The app entry point is `Home.py`; numbered files under `pages/` become sidebar
pages automatically. Keep each page importable and call `st.set_page_config`
before creating the page UI. Use `st.cache_data` only around deterministic
fetch/parse functions, keep remote URLs and credentials outside source, and
render Folium/Kepler maps through their Streamlit adapter or PyDeck maps with
`st.pydeck_chart`.

For public runtime use, preserve attribution and validate remote endpoints.
Treat WMS/XYZ/COG/housing sources and Earth Engine assets as mutable external
services. Do not claim a remote layer, asset, or timelapse exists without a
successful bounded request and an output check.

## Verification and maintenance

- Compile page files and run each bundled helper's `--help` and tiny fixture
  checks before starting a server.
- Use local GeoJSON/KML/CSV fixtures for deterministic checks; do not use a
  live remote endpoint as an import test.
- Read [repo provenance](references/repo-provenance.md) before deciding whether
  a later checkout needs `refresh-repo-skill`.
- Read [the source script map](references/source-artifact-boundaries.md) when
  adapting a page or deployment helper so the original checkout is never a
  runtime dependency.
