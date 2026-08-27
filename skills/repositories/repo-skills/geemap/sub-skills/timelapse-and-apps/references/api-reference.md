# Timelapse and App API Reference

This reference summarizes the geemap APIs owned by this sub-skill and the operational gotchas that matter in agent workflows.

## Function families

| Need | Primary API | Remote Earth Engine? | Notes |
|---|---|---:|---|
| Landsat GIF/MP4 | `geemap.landsat_timelapse` | yes | Long record from 1984; exactly 3 display bands; optional normalized-difference GIF. |
| Landsat GIF as map overlay | `geemap.Map.add_landsat_ts_gif` | yes | Uses map-drawn ROI when explicit ROI is absent; overlays GIF onto the map. |
| Sentinel-2 optical GIF/MP4 | `geemap.sentinel2_timelapse` | yes | Starts in 2015; exactly 3 bands; `cloud_pct` and cloud masking control quality. |
| Sentinel-1 SAR GIF/MP4 | `geemap.sentinel1_timelapse` | yes | Strict band combinations; orbit/filter choices matter. |
| GOES weather GIF/MP4 | `geemap.goes_timelapse` | yes | Short temporal windows; satellite and scan names are validated. |
| NAIP high-resolution GIF/MP4 | `geemap.naip_timelapse` | yes | Very small ROI recommended; optional NIR band. |
| MODIS vegetation/ocean GIF/MP4 | `geemap.modis_ndvi_timelapse`, `geemap.modis_ocean_color_timelapse` | yes | Broad regional regular-cadence products. |
| Generic ImageCollection animation | `geemap.create_timelapse` | yes | Works with a prepared `ee.ImageCollection`. |
| Dynamic World time series | `geemap.dynamic_world_timeseries` | yes | Returns an `ee.ImageCollection`; animate with `create_timelapse` or inspect on a map. |
| Local text/progress overlay | `geemap.add_text_to_gif` | no | Deterministic file operation after geemap import; no Earth Engine call. |
| Local GIF-to-MP4 | `geemap.gif_to_mp4` | no | Requires system `ffmpeg`. |
| HTML export | `Map.to_html` | maybe | Export existing interactive map to file or string. |
| Streamlit render | `Map.to_streamlit` | maybe | Requires Streamlit; folium has optional bidirectional mode. |
| Gradio HTML | `foliumap.Map.to_gradio` | maybe | Use folium backend; ipyleaflet backend prints unsupported. |
| Datapane publish | `foliumap.Map.publish` | maybe | Folium-only; requires Datapane dependency and token. |

## Remote timelapse APIs

### `geemap.landsat_timelapse`

Signature:

```python
landsat_timelapse(
    roi=None,
    out_gif=None,
    start_year=1984,
    end_year=None,
    start_date="06-10",
    end_date="09-20",
    bands=None,
    vis_params=None,
    dimensions=768,
    frames_per_second=5,
    crs="EPSG:3857",
    apply_fmask=True,
    nd_bands=None,
    nd_threshold=0,
    nd_palette=["black", "blue"],
    overlay_data=None,
    overlay_color="black",
    overlay_width=1,
    overlay_opacity=1.0,
    frequency="year",
    date_format=None,
    title=None,
    title_xy=("2%", "90%"),
    add_text=True,
    text_xy=("2%", "2%"),
    text_sequence=None,
    font_type="arial.ttf",
    font_size=20,
    font_color="white",
    add_progress_bar=True,
    progress_bar_color="white",
    progress_bar_height=5,
    loop=0,
    mp4=False,
    fading=False,
    step=1,
) -> str
```

Important behavior:

- `roi` may be an `ee.Geometry`, `ee.Feature`, or `ee.FeatureCollection`; other values raise or print ROI errors.
- `out_gif` must end with `.gif` if supplied.
- Default bands are `['NIR', 'Red', 'Green']`; exactly three of `Blue`, `Green`, `Red`, `NIR`, `SWIR1`, `SWIR2`, `pixel_qa` are required.
- Default visualization is `min=0`, `max=0.4`, `gamma=[1,1,1]`.
- `dimensions>768` switches to a thumbnail-per-frame path before making a GIF; keep first runs at or below `768`.
- If `mp4=True`, the MP4 path is `out_gif` with `.mp4` and requires `ffmpeg`.

### `geemap.Map.add_landsat_ts_gif`

Signature:

```python
Map.add_landsat_ts_gif(
    layer_name="Timelapse",
    roi=None,
    label=None,
    start_year=1984,
    end_year=2021,
    start_date="06-10",
    end_date="09-20",
    bands=["NIR", "Red", "Green"],
    vis_params=None,
    dimensions=768,
    frames_per_second=10,
    font_size=30,
    font_color="white",
    add_progress_bar=True,
    progress_bar_color="white",
    progress_bar_height=5,
    out_gif=None,
    download=False,
    apply_fmask=True,
    nd_bands=None,
    nd_threshold=0,
    nd_palette=["black", "blue"],
)
```

Important behavior:

- If `roi` is missing, the method tries the last drawn map feature and then a built-in fallback ROI.
- The ROI is converted through GeoJSON and longitude adjustment before generating the GIF.
- The generated GIF is added back with `image_overlay`; `nd_bands` adds a second normalized-difference GIF overlay.
- Use direct `landsat_timelapse` instead when no live map overlay or download link is needed.

### `geemap.sentinel2_timelapse`

Signature:

```python
sentinel2_timelapse(
    roi=None,
    out_gif=None,
    start_year=2015,
    end_year=None,
    start_date="06-10",
    end_date="09-20",
    bands=["NIR", "Red", "Green"],
    vis_params=None,
    dimensions=768,
    frames_per_second=5,
    crs="EPSG:3857",
    apply_fmask=True,
    cloud_pct=30,
    overlay_data=None,
    overlay_color="black",
    overlay_width=1,
    overlay_opacity=1.0,
    frequency="year",
    date_format=None,
    title=None,
    title_xy=("2%", "90%"),
    add_text=True,
    text_xy=("2%", "2%"),
    text_sequence=None,
    font_type="arial.ttf",
    font_size=20,
    font_color="white",
    add_progress_bar=True,
    progress_bar_color="white",
    progress_bar_height=5,
    loop=0,
    mp4=False,
    fading=False,
    step=1,
    **kwargs,
) -> str | None
```

Band aliases are translated to Sentinel-2 bands: `Blue->B2`, `Green->B3`, `Red->B4`, `Red Edge 1->B5`, `Red Edge 2->B6`, `Red Edge 3->B7`, `NIR->B8`, `Red Edge 4->B8A`, `SWIR1->B11`, `SWIR2->B12`, `QA60->QA60`.

Important behavior:

- Requires exactly three display bands.
- `cloud_pct` filters `CLOUDY_PIXEL_PERCENTAGE` and `apply_fmask` controls QA60 cloud/cirrus masking.
- `kwargs` can set reducer, `drop_empty`, and `parallel_scale` for the underlying time-series creation.

### `geemap.sentinel1_timelapse`

Signature:

```python
sentinel1_timelapse(
    roi,
    out_gif=None,
    start_year=2015,
    end_year=None,
    start_date="01-01",
    end_date="12-31",
    bands=["VV"],
    frequency="year",
    reducer="median",
    date_format=None,
    palette="Greys",
    vis_params=None,
    dimensions=768,
    frames_per_second=10,
    crs="EPSG:3857",
    overlay_data=None,
    overlay_color="black",
    overlay_width=1,
    overlay_opacity=1.0,
    orbit=["ascending", "descending"],
    title=None,
    title_xy=("2%", "90%"),
    add_text=True,
    text_xy=("2%", "2%"),
    text_sequence=None,
    font_type="arial.ttf",
    font_size=20,
    font_color="white",
    add_progress_bar=True,
    progress_bar_color="white",
    progress_bar_height=5,
    add_colorbar=False,
    colorbar_width=6.0,
    colorbar_height=0.4,
    colorbar_label=None,
    colorbar_label_size=12,
    colorbar_label_weight="normal",
    colorbar_tick_size=10,
    colorbar_bg_color=None,
    colorbar_orientation="horizontal",
    colorbar_dpi="figure",
    colorbar_xy=None,
    colorbar_size=(300, 300),
    loop=0,
    mp4=False,
    fading=False,
    **kwargs,
) -> str
```

Important behavior:

- Valid band combinations are `['VV']`, `['VH']`, `['HH']`, `['HV']`, `['VV','VH']`, and `['HH','HV']` in either paired order.
- Default visualization is `{'min': -30, 'max': 0}` if `vis_params` is omitted.
- `orbit` values are uppercased and used to filter `orbitProperties_pass`.
- Extra keyword arguments filter Sentinel-1 collection properties through the helper filtering path.

### `geemap.goes_timelapse`

Signature:

```python
goes_timelapse(
    roi=None,
    out_gif=None,
    start_date="2021-10-24T14:00:00",
    end_date="2021-10-25T01:00:00",
    data="GOES-17",
    scan="full_disk",
    bands=None,
    dimensions=768,
    framesPerSecond=10,
    date_format="YYYY-MM-dd HH:mm",
    xy=("3%", "3%"),
    text_sequence=None,
    font_type="arial.ttf",
    font_size=20,
    font_color="#ffffff",
    add_progress_bar=True,
    progress_bar_color="white",
    progress_bar_height=5,
    loop=0,
    crs=None,
    overlay_data=None,
    overlay_color="black",
    overlay_width=1,
    overlay_opacity=1.0,
    mp4=False,
    fading=False,
    **kwargs,
)
```

Important behavior:

- Default bands are `['CMI_C02', 'CMI_GREEN', 'CMI_C01']`.
- `data` is validated against supported GOES satellite names; `scan` must be `full_disk`, `conus`, or `mesoscale`.
- If `crs` is omitted and overlay data is provided, the function uses `EPSG:3857` for more reliable overlay rendering.
- The function prints collection size, then downloads an Earth Engine video and annotates dates locally.

### `geemap.naip_timelapse`

Common signature shape:

```python
naip_timelapse(
    roi,
    start_year=2003,
    end_year=None,
    out_gif=None,
    bands=None,
    palette=None,
    vis_params=None,
    dimensions=768,
    frames_per_second=3,
    crs="EPSG:3857",
    overlay_data=None,
    overlay_color="black",
    overlay_width=1,
    overlay_opacity=1.0,
    title=None,
    title_xy=("2%", "90%"),
    add_text=True,
    text_xy=("2%", "2%"),
    text_sequence=None,
    font_type="arial.ttf",
    font_size=20,
    font_color="white",
    add_progress_bar=True,
    progress_bar_color="white",
    progress_bar_height=5,
    loop=0,
    mp4=False,
    fading=False,
    step=1,
) -> str
```

Important behavior:

- Uses USDA NAIP imagery and yearly frequency.
- If NIR band `N` is requested, the image collection is filtered to four-band NAIP.
- Use very small ROIs because NAIP is high resolution.

### `geemap.modis_ndvi_timelapse`

Common signature shape:

```python
modis_ndvi_timelapse(
    roi=None,
    out_gif=None,
    data="Terra",
    band="NDVI",
    start_date=None,
    end_date=None,
    dimensions=768,
    framesPerSecond=10,
    crs="EPSG:3857",
    xy=("3%", "3%"),
    text_sequence=None,
    font_type="arial.ttf",
    font_size=20,
    font_color="#ffffff",
    add_progress_bar=True,
    progress_bar_color="white",
    progress_bar_height=5,
    loop=0,
    overlay_data=None,
    overlay_color="black",
    overlay_width=1,
    overlay_opacity=1.0,
    mp4=False,
    fading=False,
    **kwargs,
)
```

Important behavior:

- `data` is typically `Terra` or `Aqua`.
- `band` is `NDVI` or `EVI`.
- Use MODIS for broad-area, regular-cadence animations where moderate spatial resolution is acceptable.

### `geemap.dynamic_world_timeseries`

Signature:

```python
dynamic_world_timeseries(
    region,
    start_date="2016-01-01",
    end_date="2021-12-31",
    cloud_pct=30,
    frequency="year",
    reducer="mode",
    drop_empty=True,
    date_format=None,
    return_type="hillshade",
    parallel_scale=1,
) -> ee.ImageCollection
```

Important behavior:

- `region` must be an `ee.Geometry`, `ee.Feature`, or `ee.FeatureCollection`.
- `cloud_pct` must be between 0 and 100.
- `return_type` must be one of `hillshade`, `visualize`, `class`, or `probability`.
- The returned collection is not a local file; inspect it on a map or pass it to `create_timelapse`.

### `geemap.create_timelapse`

Use this when the user already has an `ee.ImageCollection` or a collection ID.

Key parameters:

```python
create_timelapse(
    collection,
    start_date,
    end_date,
    region=None,
    bands=None,
    frequency="year",
    reducer="median",
    date_format=None,
    out_gif=None,
    palette=None,
    vis_params=None,
    dimensions=768,
    frames_per_second=10,
    crs="EPSG:3857",
    overlay_data=None,
    title=None,
    add_text=True,
    add_colorbar=False,
    loop=0,
    mp4=False,
    fading=False,
    parallel_scale=1,
    step=1,
)
```

Important behavior:

- `collection` may be an `ee.ImageCollection` object or asset ID string.
- `frequency` supports `year`, `quarter`, `month`, `week`, `day`, `hour`, `minute`, and `second` through the shared time-series helper.
- `reducer` is looked up as an Earth Engine reducer name; invalid names raise.
- Single-band animations can use `palette`; three-band animations should not include a palette.

## Local GIF APIs

### `geemap.add_text_to_gif`

Signature:

```python
add_text_to_gif(
    in_gif,
    out_gif,
    xy=None,
    text_sequence=None,
    font_type="arial.ttf",
    font_size=20,
    font_color="#000000",
    add_progress_bar=True,
    progress_bar_color="white",
    progress_bar_height=5,
    duration=100,
    loop=0,
) -> None
```

Important behavior:

- Missing `in_gif` prints an error and returns without raising.
- `xy` may be integer pixels `(10, 10)` or percentage strings `('10%', '10%')`.
- `text_sequence=None` numbers frames from `1`; an integer or numeric string starts a sequence; a nonnumeric string repeats the same label; a list must match frame count.
- `font_type='arial.ttf'` uses geemap's packaged default. `alibaba.otf` is also handled specially. Other font names/paths fall back to default if not found.
- Colors are validated through geemap color checking.

### `geemap.gif_to_mp4`

Signature:

```python
gif_to_mp4(in_gif, out_mp4) -> None
```

Important behavior:

- Raises `FileNotFoundError` if the GIF is missing.
- Adds `.mp4` extension if needed and creates the output directory.
- Requires system `ffmpeg`; without it the function prints a message and returns.
- Odd GIF width or height is scaled to an even value before MP4 encoding.

## Map and app APIs

### ipyleaflet-style `geemap.Map.to_html`

Signature:

```python
Map.to_html(filename=None, title="My Map", width="100%", height="880px", add_layer_control=True, **kwargs)
```

Important behavior:

- If `filename` is provided it must end in `.html`.
- If `filename` is omitted it writes a temporary file, reads it back, deletes it, and returns the HTML string.
- `width` must be a string ending in `px` or `%`.
- `height` must be a string ending in `px`.
- If `add_layer_control=True`, a layer control is added if one is missing.

### folium `Map.to_html`

Signature:

```python
folium_map.to_html(filename=None, **kwargs) -> str | None
```

Important behavior:

- If a filename is provided, it must end in `.html` and the method writes the file.
- If no filename is provided, it returns an HTML string.
- Adds layer control when the map options request it.

### `Map.to_streamlit`

ipyleaflet-style signature:

```python
Map.to_streamlit(width=None, height=600, scrolling=False, **kwargs)
```

Folium signature:

```python
folium_map.to_streamlit(
    width=None,
    height=600,
    scrolling=False,
    add_layer_control=True,
    bidirectional=False,
    **kwargs,
)
```

Important behavior:

- Requires Streamlit import at runtime.
- Folium `bidirectional=True` imports `streamlit_folium` and returns interaction state.
- Without bidirectional mode, maps are rendered as static HTML components.

### `folium_map.to_gradio`

Signature:

```python
folium_map.to_gradio(width="100%", height="500px", **kwargs) -> str
```

Important behavior:

- Supported on folium backend.
- Converts integer width/height to pixel strings.
- Removes or warns about HTML blocks unsupported by Gradio iframe rendering.
- ipyleaflet `geemap.Map.to_gradio` is unsupported and advises switching to folium.

### `folium_map.publish`

Signature:

```python
folium_map.publish(
    name="Folium Map",
    description="",
    source_url="",
    tags=None,
    source_file=None,
    open=True,
    formatting=None,
    token=None,
    **kwargs,
)
```

Important behavior:

- Requires the Datapane package.
- If `token` is omitted, it tries existing Datapane state or the `DP_TOKEN` environment variable.
- This method is folium-only in the inspected API. If unavailable, export HTML instead.
