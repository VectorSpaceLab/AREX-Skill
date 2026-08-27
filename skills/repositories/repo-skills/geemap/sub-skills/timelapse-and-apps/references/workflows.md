# Timelapse and App Workflows

Use these recipes as self-contained operating patterns. They deliberately separate safe local file processing from Earth Engine timelapse generation and from app deployment.

## Deterministic local GIF/MP4 workflows

Local workflows operate on files that already exist. They do not need Earth Engine credentials and should not call Earth Engine APIs.

### Inspect an existing GIF

```bash
python sub-skills/timelapse-and-apps/scripts/gif_tool.py inspect animation.gif
```

Expected output includes width, height, frame count, duration metadata, and loop count when available.

### Create a tiny fixture GIF for smoke checks

```bash
python sub-skills/timelapse-and-apps/scripts/gif_tool.py fixture tiny.gif --frames 4 --size 96x64
python sub-skills/timelapse-and-apps/scripts/gif_tool.py inspect tiny.gif
```

Use this only for local script verification or demonstrations. It is not a remote sensing product.

### Add labels and a progress bar to an existing GIF

```bash
python sub-skills/timelapse-and-apps/scripts/gif_tool.py annotate input.gif labeled.gif \
  --text-sequence 2019,2020,2021,2022 \
  --xy 4%,6% \
  --font-size 18 \
  --font-color white \
  --progress-bar \
  --progress-bar-color '#00aaff'
```

Rules:

- `--text-sequence` length must match the GIF frame count unless a single `--text` or `--start-number` is used.
- `--xy` can be pixel coordinates such as `10,12` or percentages such as `4%,6%`.
- If a custom font is unreliable, omit `--font-type` and let geemap use its packaged default font.

### Convert GIF to MP4

```bash
python sub-skills/timelapse-and-apps/scripts/gif_tool.py to-mp4 labeled.gif labeled.mp4
```

This requires the system `ffmpeg` executable. The geemap conversion path automatically scales odd GIF dimensions to even dimensions for H.264-compatible MP4 output.

## Remote Earth Engine timelapse workflows

Remote timelapse functions download frames or video thumbnails from Earth Engine and then apply local GIF post-processing. Always initialize Earth Engine first, keep the first run small, and expand only after the small run succeeds.

### Common remote setup

```python
import ee
import geemap

# Use an authenticated project when the Earth Engine client requires one.
ee.Initialize(project="YOUR_EE_PROJECT")

# Prefer a tight, explicit ROI for timelapse generation.
roi = ee.Geometry.BBox(-115.47, 35.89, -114.27, 36.41)
```

If the user wants to draw the ROI interactively, construct the map in a notebook/UI context and use `Map.user_roi` or the last drawn feature only after the user has drawn a polygon/rectangle. General map setup belongs to [../../interactive-earth-engine-maps/SKILL.md](../../interactive-earth-engine-maps/SKILL.md).

### Landsat annual or seasonal timelapse

```python
out_gif = geemap.landsat_timelapse(
    roi=roi,
    out_gif="landsat_las_vegas.gif",
    start_year=1985,
    end_year=2021,
    start_date="06-10",
    end_date="09-20",
    bands=["NIR", "Red", "Green"],
    vis_params={"bands": ["NIR", "Red", "Green"], "min": 0, "max": 0.4, "gamma": [1, 1, 1]},
    dimensions=768,
    frames_per_second=5,
    title="Landsat Timelapse",
    font_color="white",
    add_progress_bar=True,
    progress_bar_color="white",
    mp4=False,
)
```

Guidance:

- Valid Landsat bands are `Blue`, `Green`, `Red`, `NIR`, `SWIR1`, `SWIR2`, and `pixel_qa`; normal RGB-like timelapses require exactly three bands.
- Landsat starts in 1984. Keep `start_year` and `end_year` within the available range and use month-day strings such as `06-10`.
- `apply_fmask=True` removes clouds, shadows, snow, and water according to the source Landsat QA mask; disable only when those masks remove too much data.
- Optional normalized-difference GIFs use `nd_bands=["Green", "SWIR1"]` or another two-band combination plus `nd_threshold` and `nd_palette`.

### Add a Landsat timelapse back onto an interactive map

```python
Map = geemap.Map()
Map.add_basemap("HYBRID")

Map.add_landsat_ts_gif(
    layer_name="Timelapse",
    roi=roi,  # or use Map.user_roi after drawing
    label="Urban Growth",
    start_year=1985,
    end_year=2021,
    start_date="06-10",
    end_date="09-20",
    bands=["NIR", "Red", "Green"],
    dimensions=768,
    frames_per_second=8,
    font_color="white",
    progress_bar_color="blue",
    download=False,
)
Map
```

Use this route only when the output needs to appear as an image overlay on a live map. Direct file generation with `landsat_timelapse` is simpler for batch or script workflows.

### Sentinel-2 optical timelapse

```python
out_gif = geemap.sentinel2_timelapse(
    roi=roi,
    out_gif="sentinel2.gif",
    start_year=2018,
    end_year=2022,
    start_date="06-01",
    end_date="09-30",
    bands=["NIR", "Red", "Green"],
    cloud_pct=20,
    frequency="year",
    dimensions=768,
    frames_per_second=5,
    title="Sentinel-2 Timelapse",
    add_progress_bar=True,
)
```

Guidance:

- Sentinel-2 starts in 2015. Use short date windows and `cloud_pct` to control clouds.
- Named bands are translated to Sentinel-2 IDs: `Blue`, `Green`, `Red`, `Red Edge 1`, `Red Edge 2`, `Red Edge 3`, `NIR`, `Red Edge 4`, `SWIR1`, `SWIR2`, `QA60`.
- The timelapse function requires exactly three visualization bands.

### Sentinel-1 SAR timelapse

```python
out_gif = geemap.sentinel1_timelapse(
    roi=roi,
    out_gif="sentinel1.gif",
    start_year=2019,
    end_year=2019,
    start_date="04-01",
    end_date="08-01",
    bands=["VV"],
    frequency="day",
    reducer="median",
    vis_params={"min": -30, "max": 0},
    palette="Greys",
    frames_per_second=3,
    title="Sentinel-1 Timelapse",
    add_colorbar=True,
    colorbar_bg_color="gray",
)
```

Guidance:

- Valid band combinations are `['VV']`, `['VH']`, `['HH']`, `['HV']`, `['VV','VH']`, and `['HH','HV']` in either paired order.
- Orbit can be `['ascending']`, `['descending']`, or both. Use a homogeneous orbit and band combination when results flicker.
- Extra keyword filters are passed into Sentinel-1 collection filtering.

### GOES weather satellite timelapse

```python
out_gif = geemap.goes_timelapse(
    roi=roi,
    out_gif="goes.gif",
    start_date="2021-10-24T14:00:00",
    end_date="2021-10-25T01:00:00",
    data="GOES-17",
    scan="full_disk",
    bands=["CMI_C02", "CMI_GREEN", "CMI_C01"],
    dimensions=768,
    framesPerSecond=10,
    date_format="YYYY-MM-dd HH:mm",
    mp4=False,
)
```

Guidance:

- `data` must be a supported GOES satellite name such as `GOES-16` through `GOES-20`.
- `scan` must be `full_disk`, `conus`, or `mesoscale`.
- GOES timelapses can contain many frames over a short time window; reduce date span or frame rate first when requests are slow.

### NAIP high-resolution imagery timelapse

```python
out_gif = geemap.naip_timelapse(
    roi,
    start_year=2009,
    end_year=2021,
    out_gif="naip.gif",
    bands=["N", "R", "G"],
    frames_per_second=3,
    dimensions=768,
    mp4=True,
)
```

Guidance:

- NAIP is high resolution and can be large. Use a very small ROI.
- Include `"N"` in the band list only when NIR imagery is available; the helper filters for four-band NAIP when NIR is requested.

### MODIS vegetation or ocean-color timelapse

```python
out_gif = geemap.modis_ndvi_timelapse(
    roi=roi,
    out_gif="modis_ndvi.gif",
    data="Terra",
    band="NDVI",
    start_date="2018-01-01",
    end_date="2022-12-31",
    dimensions=768,
    frames_per_second=5,
    title="MODIS NDVI",
)
```

Guidance:

- MODIS is suitable when a broad region or regular cadence matters more than spatial detail.
- Route colorbar styling and static cartographic embellishments to [../../visualization-and-charts/SKILL.md](../../visualization-and-charts/SKILL.md) unless they are being embedded in the animation.

### Dynamic World time-series animation

`dynamic_world_timeseries` returns an Earth Engine `ImageCollection`; use it directly for map inspection or pass it to `create_timelapse` for a GIF.

```python
images = geemap.dynamic_world_timeseries(
    region=roi,
    start_date="2018-01-01",
    end_date="2022-12-31",
    cloud_pct=30,
    frequency="year",
    reducer="mode",
    return_type="hillshade",
)

out_gif = geemap.create_timelapse(
    images,
    start_date="2018-01-01",
    end_date="2022-12-31",
    region=roi,
    out_gif="dynamic_world.gif",
    bands=["vis-red", "vis-green", "vis-blue"],
    dimensions=768,
    frames_per_second=4,
    title="Dynamic World",
)
```

Guidance:

- `return_type` can be `hillshade`, `visualize`, `class`, or `probability`.
- Dynamic World depends on matching Sentinel-2 scene IDs and cloud filtering, so empty periods can occur.
- For classification analysis or AI/data catalog tasks, route to [../../machine-learning-and-ai/SKILL.md](../../machine-learning-and-ai/SKILL.md).

## Web app and publication workflows

### Save an interactive map as HTML

```python
import geemap

Map = geemap.Map(center=[40, -100], zoom=4)
# Add layers before exporting.
Map.to_html(filename="map.html", title="My Map", width="100%", height="880px")
```

`geemap.Map.to_html` requires `width` to end with `px` or `%` and `height` to end with `px`. If `filename` is omitted, it returns an HTML string instead of writing a file.

Folium backend:

```python
import geemap.foliumap as geemap

Map = geemap.Map(center=[40, -100], zoom=4)
html = Map.to_html()          # returns a string
Map.to_html("map.html")      # writes a file
```

### Streamlit app

Static component for either backend:

```python
import streamlit as st
import geemap

st.set_page_config(layout="wide")
Map = geemap.Map(center=[40, -100], zoom=4)
Map.to_streamlit(width=None, height=600, scrolling=False)
```

Folium bidirectional mode requires `streamlit-folium`:

```python
import streamlit as st
import geemap.foliumap as geemap

Map = geemap.Map(center=[40, -100], zoom=4)
st_component = Map.to_streamlit(height=600, bidirectional=True)
if st_component:
    center = Map.st_map_center(st_component)
    bounds = Map.st_map_bounds(st_component)
```

Install the app dependencies when needed with the `apps` extra. Keep ports, secrets, and Streamlit config outside the skill files.

### Gradio app

The Gradio HTML route is supported by the folium backend, not the ipyleaflet backend.

```python
import ee
import gradio as gr
import geemap.foliumap as geemap

ee.Initialize(project="YOUR_EE_PROJECT")

def render_map(vmin, vmax, palette):
    Map = geemap.Map(center=[21.79, 70.87], zoom=3)
    image = ee.Image("USGS/SRTMGL1_003")
    Map.addLayer(image, {"min": vmin, "max": vmax, "palette": palette}, "SRTM")
    return Map.to_gradio(width="100%", height="500px")

demo = gr.Interface(
    render_map,
    [gr.Number(value=0), gr.Number(value=6000), gr.Textbox(value="terrain")],
    "html",
    title="Visualize Earth Engine Data",
)
demo.launch()
```

### Voila-style notebook app

Voila serves a notebook as an app. A typical pattern is:

```bash
voila --no-browser app.ipynb
```

Then expose port `8866` through the deployment environment or a tunneling service if sharing outside the local machine. Password protection, public URLs, and tunnel tokens belong to deployment configuration.

### Solara route

The `apps` extra includes Solara. Use it when the requested deliverable is a Python app module rather than a notebook. Keep the geemap map construction in a function and let Solara own page layout, routing, and serving. If a framework-specific widget conflict appears, export to HTML or use the folium backend as a fallback.

### Folium Datapane publishing

Current geemap exposes `publish` on the folium map class. Use it only when the Datapane package and token are available.

```python
import geemap.foliumap as geemap

Map = geemap.Map(center=[40, -100], zoom=4)
Map.publish(
    name="Terrain Visualization",
    description="A folium map with Earth Engine data layers",
    token="YOUR_DATAPANE_TOKEN",  # or configure DP_TOKEN in the environment
)
```

If `publish` is missing on an ipyleaflet `geemap.Map`, switch to `geemap.foliumap.Map` or use `to_html` instead.
