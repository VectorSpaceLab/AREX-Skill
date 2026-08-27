# Timelapse and App Troubleshooting

Start by classifying the failure:

- **Local file failure**: existing GIF inspection, annotation, or MP4 conversion. No Earth Engine credentials should be involved.
- **Remote Earth Engine failure**: satellite data query, video thumbnail download, map overlay, or export timeout.
- **App/deployment failure**: HTML export, Streamlit, Gradio, Voila, Solara, Datapane, browser port, or token issue.

## Local GIF/MP4 failures

### Input GIF missing or not a GIF

Symptoms:

- `The input gif file does not exist.`
- `FileNotFoundError`
- Inspect command reports the file cannot be opened.

Fix:

1. Confirm the input path points to an existing `.gif` file.
2. Run local inspection first:

   ```bash
   python sub-skills/timelapse-and-apps/scripts/gif_tool.py inspect input.gif
   ```

3. If the file is remote, download it explicitly before using local tools.

### Text labels do not appear or annotation silently produces no file

Likely causes:

- `--text-sequence` length does not match the number of frames.
- `--xy` is outside image bounds.
- The requested font is not available.
- Output directory cannot be created.

Fix:

1. Inspect frame count first.
2. Use a single repeated `--text` label or provide one label per frame.
3. Use percentage coordinates such as `4%,6%` for portable placement.
4. Omit `--font-type` unless a known font file is required.
5. Use a writable output path ending in `.gif`.

### MP4 conversion creates no file

Likely cause: system `ffmpeg` is missing or inaccessible.

Fix:

1. Run:

   ```bash
   ffmpeg -version
   ```

2. If missing, install/provide `ffmpeg` in the runtime environment.
3. Re-run:

   ```bash
   python sub-skills/timelapse-and-apps/scripts/gif_tool.py to-mp4 input.gif output.mp4
   ```

Notes:

- Geemap scales odd GIF dimensions to even dimensions before H.264 MP4 encoding.
- If only GIF output is required, do not set `mp4=True` and do not call the MP4 conversion path.

### Color or font errors

Symptoms:

- Invalid color exception.
- Font fallback warning.
- Text is invisible due to same-color background.

Fix:

- Use named colors like `white`, `black`, `red` or hex colors like `#00aaff`.
- Increase `--font-size` for small GIFs.
- Put text at a high-contrast location and use a progress bar color distinct from the image.

## Earth Engine authentication and network failures

### Earth Engine is not initialized

Symptoms:

- Authentication prompt or credential error.
- Project/account error from the Earth Engine client.
- Requests fail before any image collection size is computed.

Fix:

1. Follow [../../../references/installation-and-auth.md](../../../references/installation-and-auth.md).
2. Initialize explicitly:

   ```python
   import ee
   ee.Initialize(project="YOUR_EE_PROJECT")
   ```

3. If running in a hosted notebook or service, make sure the service account/user credentials are available in that environment.

### Network, proxy, or Earth Engine service timeout

Symptoms:

- HTTP timeout while downloading video or thumbnails.
- Long hang at `getInfo()` or collection-size printing.
- Empty or partial GIF file.

Fix:

1. Confirm network access to Earth Engine services.
2. If a proxy is required, configure it before geemap/Earth Engine calls.
3. Shrink the request:
   - smaller ROI,
   - fewer years/dates,
   - `dimensions=512` or `768`,
   - annual instead of monthly/daily frequency,
   - lower `frames_per_second` only affects playback, not server workload, so reduce frame count first.
4. Retry once the small version works.
5. For persistent service failures, keep generated partial files for diagnosis but regenerate the output from a clean command when service access returns.

## ROI validation failures

Symptoms:

- `The provided roi is invalid. It must be an ee.Geometry`.
- `Could not convert the provided roi to ee.Geometry`.
- Timelapse covers the wrong location or huge area.

Fix:

1. Use `ee.Geometry.BBox(min_lon, min_lat, max_lon, max_lat)` or a simple polygon.
2. If using a map-drawn region, check that the user actually drew a polygon/rectangle before reading `Map.user_roi`.
3. Keep the ROI tight. Timelapse functions request video/thumbnail rendering over the whole region.
4. For geometry crossing the antimeridian, use a geometry that geemap can convert and adjust, or split the ROI.
5. Route general drawing/map UI setup to [../../interactive-earth-engine-maps/SKILL.md](../../interactive-earth-engine-maps/SKILL.md).

## Date range, band, and filter failures

### Landsat

Common issues:

- `start_year` earlier than 1984.
- `end_year` later than the current year.
- `start_date`/`end_date` not formatted as `MM-DD`.
- Bands are not exactly three of the allowed Landsat display bands.

Fix:

- Use years within the Landsat record.
- Use strings such as `06-10` and `09-20`.
- Start with `bands=['NIR','Red','Green']` and default `vis_params`.
- If too many cloudy/empty frames appear, keep `apply_fmask=True`, narrow the seasonal date window, or switch frequency/date span.

### Sentinel-2

Common issues:

- Year before 2015.
- Too strict `cloud_pct` creates empty composites.
- More or fewer than three display bands.
- Mixing Sentinel band IDs and aliases inconsistently.

Fix:

- Start with `bands=['NIR','Red','Green']`, `cloud_pct=30`, and a known cloudy-season-aware date window.
- Increase `cloud_pct` if empty periods occur.
- Use `parallel_scale` through `kwargs` if reductions run out of memory.

### Sentinel-1

Common issues:

- Invalid band combination.
- Orbit directions mixed across an area where ascending/descending images differ strongly.
- Extra collection-property filters remove all images.

Fix:

- Use `bands=['VV']` first.
- Try one orbit at a time: `orbit=['ascending']` or `orbit=['descending']`.
- Remove extra filters until a basic timelapse works.
- Use `vis_params={'min': -30, 'max': 0}` and `palette='Greys'` as a stable starting point.

### GOES

Common issues:

- Unsupported `data` satellite name.
- Invalid `scan` value.
- Too many frames from a long high-frequency window.

Fix:

- Use a supported GOES satellite name and `scan` in `full_disk`, `conus`, or `mesoscale`.
- Begin with a few hours, then expand.
- Use default GOES RGB bands unless the user requests a specific channel combination.

### NAIP

Common issues:

- ROI too large for high-resolution imagery.
- Requested NIR band is unavailable for some years/areas.
- Sparse acquisition years produce missing frames.

Fix:

- Use a city-block to neighborhood-sized ROI for first run.
- Use RGB bands first; request `N` only when needed.
- Expand year range only after confirming frames exist.

### MODIS

Common issues:

- Expecting high-resolution local detail.
- Wrong data source or band choice.

Fix:

- Use MODIS for broad regions and regular time series.
- Use `data='Terra'` or `data='Aqua'`, and `band='NDVI'` or `band='EVI'` for NDVI/EVI workflows.

### Dynamic World

Common issues:

- `cloud_pct` outside 0-100.
- Invalid `return_type`.
- Empty scene matches from Sentinel-2 filtering.

Fix:

- Use `return_type='hillshade'` first.
- Relax `cloud_pct` or expand the date range.
- For non-animation classification analysis, route to [../../machine-learning-and-ai/SKILL.md](../../machine-learning-and-ai/SKILL.md).

## Overlay, text, progress bar, and colorbar failures

Symptoms:

- Boundary overlay missing or misplaced.
- Text not visible.
- Colorbar missing from Sentinel-1/generic timelapse.
- Progress bar overlaps important content.

Fix:

1. Confirm overlay data is an Earth Engine-compatible feature/geometry or supported boundary identifier.
2. Use `overlay_color`, `overlay_width`, and `overlay_opacity` with high contrast.
3. For GOES with overlays, allow `crs='EPSG:3857'` or omit `crs` so geemap chooses a safer CRS.
4. Move labels with `title_xy`, `text_xy`, or `xy` percentage coordinates.
5. For colorbar-heavy or static cartographic design, route to [../../visualization-and-charts/SKILL.md](../../visualization-and-charts/SKILL.md) unless the colorbar is embedded in the GIF.

## Large export and output-size failures

Symptoms:

- Very slow frame generation.
- Earth Engine memory errors.
- Empty output or partial frames.
- Local disk fills with temporary thumbnails.

Fix:

1. Reduce ROI.
2. Use `dimensions=512` or `768` first.
3. Reduce date span or switch to coarser `frequency`.
4. Use `step` to skip periods when supported.
5. Use `parallel_scale` on generic/Sentinel-2/Dynamic World workflows when reductions are memory-heavy.
6. Avoid `dimensions>768` until the small output works; that path downloads individual thumbnails and then builds a GIF locally.
7. Use `mp4=False` until GIF generation succeeds.

## HTML export failures

Symptoms:

- `The output file extension must be html.`
- `width must end with px or %`.
- `height must end with px`.
- Map exported without expected controls.

Fix:

- Use `filename='map.html'`.
- Set `width='100%'` or `width='900px'`.
- Set `height='600px'` or another pixel string.
- Pass `add_layer_control=True` for ipyleaflet maps when layer toggles are needed.
- Use folium backend for static web output when ipywidgets are not supported by the target host.

## Streamlit failures

Symptoms:

- `ModuleNotFoundError: streamlit`.
- `ModuleNotFoundError: streamlit_folium` when `bidirectional=True`.
- Map displays but interactions are not returned to Python.
- Port already in use.

Fix:

1. Install app extras or the specific missing package.
2. Use non-bidirectional `Map.to_streamlit(...)` if interaction state is not required.
3. Use folium backend and `bidirectional=True` only when `streamlit-folium` is available.
4. Choose a free Streamlit port in deployment configuration.
5. Keep secrets and Earth Engine credentials in Streamlit secrets/environment configuration, not in the code.

## Gradio failures

Symptoms:

- ipyleaflet map says Gradio is unsupported.
- HTML iframe appears blank.
- JavaScript function warnings appear.

Fix:

1. Use `import geemap.foliumap as geemap`.
2. Return `Map.to_gradio()` from the Gradio function and use output type `html`.
3. Avoid map elements that embed unsupported JavaScript callbacks.
4. If a layer/control is incompatible with Gradio iframe rendering, export HTML with `to_html` or simplify the folium map.

## Voila, Solara, and port-sharing failures

Symptoms:

- App starts locally but cannot be reached by others.
- Port `8866` or the selected port is unavailable.
- Notebook code cells appear or hidden code is needed for debugging.
- Widget state does not update.

Fix:

1. Confirm the app runs locally first.
2. Select a free port or stop the conflicting process.
3. Configure the host, reverse proxy, or tunnel to expose the port.
4. For Voila, choose whether to strip sources based on the desired public view.
5. For Solara, keep map construction framework-friendly and fall back to folium/HTML export if widget models conflict.

## Datapane publish failures

Symptoms:

- `ModuleNotFoundError: datapane`.
- Token/login error.
- `publish` method missing.

Fix:

1. Use `geemap.foliumap.Map`, not ipyleaflet `geemap.Map`, for `publish`.
2. Install/provide Datapane only when publication is requested.
3. Provide `token=` or configure `DP_TOKEN`.
4. If publication remains blocked, export `map.html` with `to_html` and hand off the HTML artifact.

## Choosing the next fallback

- If Earth Engine auth/network is unavailable, do **not** attempt remote timelapse generation. Prepare the code and run local GIF workflows only.
- If remote generation works but annotation fails, keep the raw GIF and apply [scripts/gif_tool.py](../scripts/gif_tool.py) locally.
- If MP4 conversion fails, deliver GIF and note missing `ffmpeg`.
- If app deployment fails, deliver an HTML export and list the missing optional extra, token, or port constraint.
