# Installation and Authentication

Use this reference before running geemap code, especially when a workflow touches Earth Engine, Jupyter widgets, optional visualization backends, or cloud/network services.

## Package installation

Base install:

```bash
pip install geemap
```

Conda-forge install:

```bash
conda install -c conda-forge geemap
```

Development or local-checkout install for maintainers:

```bash
pip install -e .
```

The package metadata requires Python 3.12 or newer for this snapshot. If users follow older tutorials that mention older Python versions, prefer the package metadata and the installed package version.

## Minimal import and map smoke

Use a no-auth smoke first when the task is only about package availability or local map construction:

```bash
python - <<'PY'
import geemap
print(geemap.__version__)
Map = geemap.Map(center=[40, -100], zoom=4, ee_initialize=False)
print(type(Map).__name__)
PY
```

For a reusable command-line check, run:

```bash
python path/to/this/skill/scripts/check_geemap_env.py --skip-ee-auth
```

## Earth Engine authentication and projects

Real Earth Engine objects, map tiles, reducers, exports, timelapses, and most catalog-backed workflows require a Google Earth Engine account, network access, and a project that is authorized for Earth Engine.

Typical pattern:

```python
import ee
import geemap

ee.Authenticate()      # interactive; run once per environment when needed
ee.Initialize(project="your-ee-project")
Map = geemap.Map(center=[40, -100], zoom=4)
```

When writing reusable code for unknown environments:

- Accept a `project` parameter instead of hard-coding a project ID.
- Use `ee_initialize=False` when constructing maps for offline layout, UI, or tests.
- Surface auth/project failures as setup issues, not as geemap API failures.
- Avoid `getInfo()` on large objects; prefer export tasks, thumbnails, or sampled reductions.

## Backend choice: ipyleaflet versus folium

Default top-level `import geemap` uses the ipyleaflet-backed map unless the `USE_FOLIUM` environment variable is set.

```python
import geemap
m = geemap.Map(ee_initialize=False)  # ipyleaflet-backed by default
```

For folium-first HTML/static use, either set the environment variable before importing geemap or import the folium module explicitly:

```bash
USE_FOLIUM=1 python your_script.py
```

```python
import geemap.foliumap as geemap
m = geemap.Map(ee_initialize=False)
```

The folium backend is often better for standalone HTML and some Streamlit/Gradio routes. The ipyleaflet backend is better for notebook widgets, inspectors, layer managers, drawing controls, and interactive Earth Engine exploration.

## Optional extras map

Install the smallest extra that matches the requested workflow:

| Need | Extra or package |
|---|---|
| pydeck or kepler.gl visual backends | `geemap[backends]` |
| Local raster/COG workflows with local tiles | `geemap[raster]` |
| GeoPandas, OSM, or vector processing | `geemap[vector]` |
| PostGIS/SQL workflows | `geemap[sql]` |
| Streamlit, Gradio, Voila, Solara app routes | `geemap[apps]` |
| Gemini, LangChain, Google AI/Cloud dataset search helpers | `geemap[ai]` |
| LiDAR/3D point cloud notebooks | `geemap[lidar]` |

Do not install `geemap[all]` by default. It is convenient for broad demos but can pull compiled geospatial packages, large UI stacks, and cloud/AI dependencies that are unnecessary for many tasks.

## Network and proxy setup

Earth Engine, Google Cloud, OSM, STAC/titiler, Planet, MapTiler, and remote COG requests require network access. If the user is behind a proxy, geemap exposes:

```python
import geemap
geemap.set_proxy(port=1080, ip="http://127.0.0.1", timeout=300)
```

Use the user's actual proxy configuration only in their runtime environment; do not embed private proxy values into scripts or notebooks.

## Jupyter and widget notes

- Restart the Jupyter kernel or Colab runtime after installing or upgrading geemap if imports fail immediately after installation.
- ipyleaflet/ipywidgets output requires a compatible notebook frontend.
- Folium maps can be saved to HTML and are less dependent on live widget comms.
- If a widget is blank, first check the backend choice, frontend extension support, browser console errors, and whether the object was displayed as the final cell result.
