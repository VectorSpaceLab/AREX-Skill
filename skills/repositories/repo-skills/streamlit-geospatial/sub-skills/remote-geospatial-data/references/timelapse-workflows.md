# Timelapse workflows

Choose one family before calling a generator. These operations are remote and
can also create local GIF/MP4 artifacts; a local signature check is not a live
Earth Engine verification. Start with a small sample ROI and short date span,
then expand one bound at a time.

## Shared preflight

1. Validate a closed, non-empty GeoJSON geometry and a forward date range with
   `scripts/validate_ee_config.py`. For a sample ROI, use the page's small
   WGS84 polygons or an equivalent caller-owned fixture.
2. Convert the ROI with `geemap.gdf_to_ee(gdf, geodesic=False)` after checking
   CRS and geometry. `roi=None` is accepted by several installed generators,
   but an explicit small ROI is safer and makes cost/coverage observable.
3. Set `USE_FOLIUM=1` before importing `geemap.foliumap`; authenticate only at
   the approved service boundary.
4. Set a caller-selected `.gif` output path. Request MP4 only after confirming
   `ffmpeg` is available; use GIF reduction only after confirming `gifsicle` or
   the package's compatible optimization path. After generation, check that
   the GIF exists and, when requested, that the sibling MP4 exists.
5. Keep `dimensions`, frame rate, frequency, date span, and ROI bounded. The
   page uses dimensions 768 for its remote generators even when a larger UI
   value is offered.

## Landsat and Sentinel-2

Use these when the question is a seasonal or periodic optical surface
reflectance sequence. The installed signatures are:

```python
geemap.landsat_timelapse(
    roi=None, out_gif=None, start_year=1984, end_year=None,
    start_date="06-10", end_date="09-20",
    bands=["NIR", "Red", "Green"], vis_params=None,
    dimensions=768, frames_per_second=5, crs="EPSG:3857",
    apply_fmask=True, nd_bands=None, nd_threshold=0,
    nd_palette=["black", "blue"], overlay_data=None,
    overlay_color="black", overlay_width=1, overlay_opacity=1.0,
    frequency="year", date_format=None, title=None,
    title_xy=("2%", "90%"), add_text=True, text_xy=("2%", "2%"),
    text_sequence=None, font_type="arial.ttf", font_size=20,
    font_color="white", add_progress_bar=True,
    progress_bar_color="white", progress_bar_height=5, loop=0,
    mp4=False, fading=False, step=1,
)

geemap.sentinel2_timelapse(
    roi=None, out_gif=None, start_year=2015, end_year=None,
    start_date="06-10", end_date="09-20",
    bands=["NIR", "Red", "Green"], vis_params=None,
    dimensions=768, frames_per_second=5, crs="EPSG:3857",
    apply_fmask=True, cloud_pct=30, overlay_data=None,
    overlay_color="black", overlay_width=1, overlay_opacity=1.0,
    frequency="year", date_format=None, title=None,
    title_xy=("2%", "90%"), add_text=True, text_xy=("2%", "2%"),
    text_sequence=None, font_type="arial.ttf", font_size=20,
    font_color="white", add_progress_bar=True,
    progress_bar_color="white", progress_bar_height=5, loop=0,
    mp4=False, fading=False, step=1, **kwargs,
)
```

Use `landsat_timelapse` for Landsat (start year no earlier than 1984 in the
page) and `sentinel2_timelapse` for Sentinel-2 (start year no earlier than
2015). The app routes bands such as `Red/Green/Blue`, `NIR/Red/Green`, and
SWIR combinations, supports yearly/quarterly/monthly frequency, enables cloud
masking by default, and uses an optional overlay. Treat the page's month
construction as UI input, not as permission to create an invalid date (for
example, validate month/day combinations before execution).

## Generic Earth Engine ImageCollection

Use `create_timelapse` only when the caller has a known collection and has
selected compatible bands, reducer, and visualization. The installed
signature is:

```python
geemap.create_timelapse(
    collection, start_date: str, end_date: str, region=None, bands=None,
    frequency="year", reducer="median", date_format=None, out_gif=None,
    palette=None, vis_params=None, dimensions=768, frames_per_second=10,
    crs="EPSG:3857", overlay_data=None, overlay_color="black",
    overlay_width=1, overlay_opacity=1.0, title=None,
    title_xy=("2%", "90%"), add_text=True, text_xy=("2%", "2%"),
    text_sequence=None, font_type="arial.ttf", font_size=20,
    font_color="white", add_progress_bar=True,
    progress_bar_color="white", progress_bar_height=5,
    add_colorbar=False, colorbar_width=6.0, colorbar_height=0.4,
    colorbar_label=None, colorbar_label_size=12,
    colorbar_label_weight="normal", colorbar_tick_size=10,
    colorbar_bg_color=None, colorbar_orientation="horizontal",
    colorbar_dpi="figure", colorbar_xy=None, colorbar_size=(300, 300),
    loop=0, mp4=False, fading=False, parallel_scale=1, step=1,
)
```

The page searches catalog metadata, loads the chosen ID, probes the first
image bands, and then calls this helper with `frequency` (year/quarter/month/
other supported units), a reducer such as `median`, bands, palette, and
`vis_params`. Reject an unknown asset type, no selected band, or a malformed
visualization object before this call.

## GOES

Use GOES for short, high-frequency geostationary sequences. The installed
signature is:

```python
geemap.goes_timelapse(
    roi=None, out_gif=None,
    start_date="2021-10-24T14:00:00",
    end_date="2021-10-25T01:00:00", data="GOES-17",
    scan="full_disk", bands=["CMI_C02", "CMI_GREEN", "CMI_C01"],
    dimensions=768, framesPerSecond=10,
    date_format="YYYY-MM-dd HH:mm", xy=("3%", "3%"),
    text_sequence=None, font_type="arial.ttf", font_size=20,
    font_color="#ffffff", add_progress_bar=True,
    progress_bar_color="white", progress_bar_height=5, loop=0,
    crs=None, overlay_data=None, overlay_color="black",
    overlay_width=1, overlay_opacity=1.0, mp4=False,
    fading=False, **kwargs,
)
```

Use an ISO datetime interval, select a supported satellite and scan mode, and
bound the interval tightly. The page offers GOES-17/GOES-16 and full-disk,
CONUS, or mesoscale choices. A long interval or a full-disk request can be
expensive even when the ROI is small. If hotspot characterization is also
requested, treat it as a separate optional remote operation; do not claim it
succeeded because the base timelapse succeeded.

## MODIS NDVI/EVI

Use the installed positional contract only after normalizing dates and band:

```python
geemap.modis_ndvi_timelapse(
    roi=None, out_gif=None, data="Terra", band="NDVI",
    start_date=None, end_date=None, dimensions=768,
    framesPerSecond=10, crs="EPSG:3857", xy=("3%", "3%"),
    text_sequence=None, font_type="arial.ttf", font_size=20,
    font_color="#ffffff", add_progress_bar=True,
    progress_bar_color="white", progress_bar_height=5, loop=0,
    overlay_data=None, overlay_color="black", overlay_width=1,
    overlay_opacity=1.0, mp4=False, fading=False, **kwargs,
)
```

The page selects `Terra` or `Aqua`, `NDVI` or `EVI`, and a date range, then
passes ROI and output as the first two arguments. A global or many-year request
should be split or reduced before execution.

## MODIS ocean color and other generic MODIS collections

For ocean color, the installed signature is:

```python
geemap.modis_ocean_color_timelapse(
    satellite, start_date, end_date, roi=None, bands=None,
    frequency="year", reducer="median", date_format=None,
    out_gif=None, palette="coolwarm", vis_params=None,
    dimensions=768, frames_per_second=5, crs="EPSG:3857",
    overlay_data=None, overlay_color="black", overlay_width=1,
    overlay_opacity=1.0, title=None, title_xy=("2%", "90%"),
    add_text=True, text_xy=("2%", "2%"), text_sequence=None,
    font_type="arial.ttf", font_size=20, font_color="white",
    add_progress_bar=True, progress_bar_color="white",
    progress_bar_height=5, add_colorbar=True, colorbar_width=6.0,
    colorbar_height=0.4, colorbar_label="Sea Surface Temperature (°C)",
    colorbar_label_size=12, colorbar_label_weight="normal",
    colorbar_tick_size=10, colorbar_bg_color="white",
    colorbar_orientation="horizontal", colorbar_dpi="figure",
    colorbar_xy=None, colorbar_size=(300, 300), loop=0,
    mp4=False, fading=False,
)
```

Pass the satellite identifier, ISO dates, ROI, selected bands, and an already
validated `vis_params` dict. For MODIS land-surface-temperature or another
known collection, use `create_timelapse` with its asset and compatible bands;
do not silently route it through the ocean-color helper.

## NAIP

Use NAIP for a U.S.-focused aerial imagery sequence. The installed signature
is:

```python
geemap.naip_timelapse(
    roi, start_year: int | str = 2003, end_year: int | str | None = None,
    out_gif: str | None = None, bands: list[str] | None = None,
    palette=None, vis_params=None, dimensions=768,
    frames_per_second: int = 3, crs="EPSG:3857", overlay_data=None,
    overlay_color="black", overlay_width=1, overlay_opacity=1.0,
    title=None, title_xy=("2%", "90%"), add_text=True,
    text_xy=("2%", "2%"), text_sequence=None, font_type="arial.ttf",
    font_size=20, font_color="white", add_progress_bar=True,
    progress_bar_color="white", progress_bar_height=5, loop=0,
    mp4=False, fading: bool | int = False, step=1,
)
```

The page chooses `N/R/G` or `R/G/B`, uses dimensions 768, and passes the ROI
positionally. Restrict the ROI to the U.S. coverage area and expect gaps
between acquisition years.

## Output and bounded-size policy

A GIF path is not evidence of valid imagery until the generator returns and the
file exists. If `mp4=True`, verify the sibling MP4 path and report conversion
failure separately from Earth Engine failure. Keep `dimensions` at or below the
caller-approved bound (the evidence uses 768), use a small ROI, reduce the date
span or frequency, and lower frame rate/step when the operation is too large.
Do not automatically retry an expensive request unchanged.
