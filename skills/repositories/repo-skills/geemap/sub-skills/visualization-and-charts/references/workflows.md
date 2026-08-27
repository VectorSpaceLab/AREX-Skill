# Visualization and chart workflows

This reference is self-contained for geemap visualization work. It assumes geemap is installed; authenticate Earth Engine only for workflows that read Earth Engine objects remotely.

## 1. Local charts and safe chart helpers

Use local chart helpers when the data is already in memory or when you need deterministic checks without Earth Engine credentials.

```python
import pandas as pd
from geemap import chart

# Date conversion is handled by DataTable.
dt = chart.DataTable(
    {"date": ["2024-01-01", "2024-02-01"], "ndvi": [0.25, 0.41]},
    date_column="date",
)

# Convert nested arrays to a table and render with bqplot.
df = chart.array_to_df(
    [[0.2, 0.4, 0.5], [0.3, 0.35, 0.6]],
    x_values=[1, 2, 3],
    y_labels=["site_a", "site_b"],
    x_label="month",
)
c = chart.Chart(df, chart_type="LineChart", x_cols=["month"], y_cols=["site_a", "site_b"], title="NDVI")
c.display()
```

Supported `Chart` types include `ScatterChart`, `LineChart`, `ColumnChart`, `BarChart`, `PieChart`, `AreaChart`, `IntervalChart`, and `Table`. `BarChart` defaults to horizontal orientation unless overridden.

Local dataframe helpers:

- `chart.DataTable(data, date_column=None, date_format=None, **kwargs)` converts dictionaries, pandas DataFrames, `ee.FeatureCollection`, and `ee.List`-style table data to a pandas-backed table.
- `chart.transpose_df(df, label_col, index_name=None, indexes=None)` requires `label_col` to exist and custom `indexes` to match the transposed row count.
- `chart.pivot_df(df, index, columns, values)` returns a reset-index wide table.
- `chart.array_to_df(y_values, x_values=None, y_labels=None, x_label="x", axis=1, **kwargs)` requires `len(y_labels) == len(y series)` when labels are supplied.

## 2. Earth Engine feature charts

Feature chart wrappers produce bqplot/matplotlib-style notebook output and normally call server-side Earth Engine data retrieval. Initialize Earth Engine first.

```python
import ee
import geemap.chart as chart

ee.Initialize(project="your-ee-project")
features = ee.FeatureCollection("projects/google/charts_feature_example")

chart.feature_by_feature(
    features,
    x_property="label",
    y_properties=["value1", "value2"],
    title="Values by feature",
    colors=["#1f77b4", "#ff7f0e"],
)
```

Feature chart choices:

- `feature_by_feature(features, x_property, y_properties, **kwargs)`: one or more numeric properties per feature.
- `feature_by_property(features, x_properties, series_property, **kwargs)`: properties on the x-axis, one series per feature.
- `feature_groups(features, x_property, y_property, series_property, **kwargs)`: grouped/stacked feature chart.
- `feature_histogram(features, property, max_buckets=None, min_bucket_width=None, show=True, **kwargs)`: validates that `features` is an `ee.FeatureCollection` and that `property` exists; use `show=False` to receive the bqplot object instead of displaying immediately.

Before calling a feature chart, verify:

- the feature collection has the named properties;
- numeric properties are convertible to numbers for histograms and y-values;
- large feature collections are filtered or sampled so `getInfo()`-style transfer is bounded.

## 3. Earth Engine image and time-series charts

Image chart wrappers reduce pixels over regions or feature collections. They require a reducer and scale unless the function explicitly supplies a default.

```python
import ee
import geemap.chart as chart

ee.Initialize(project="your-ee-project")
region = ee.Geometry.Rectangle([-122.6, 37.0, -121.8, 37.7])
image = ee.Image("USGS/SRTMGL1_003")

chart.image_by_region(
    image=image,
    regions=region,
    reducer="MEAN",       # or ee.Reducer.mean()
    scale=90,
    x_property="system:index",
    title="Elevation summary",
)
```

Common chart contracts:

- `image_by_region(image, regions, reducer, scale, x_property, **kwargs)`: reduces image bands by region and plots band values.
- `image_by_class(image, class_band, region, reducer="MEAN", scale=None, class_labels=None, x_labels=None, chart_type="LineChart", **kwargs)`: summarizes by class values.
- `image_series(image_collection, region, reducer=None, scale=None, x_property="system:time_start", chart_type="LineChart", ...)`: one region over time; defaults reducer to mean when omitted.
- `image_series_by_region(image_collection, regions, reducer=None, band=None, scale=None, x_property="system:time_start", series_property="system:index", ...)`: multiple region series.
- `image_doy_series`, `image_doy_series_by_region`, and `doy_series_by_year`: day-of-year time series; set start/end day and region/year reducers explicitly for reproducibility.
- `image_histogram(image, region, scale, max_buckets, min_bucket_width, max_raw, max_pixels, reducer_args={}, **kwargs)`: strict histogram inputs; set `maxPixels` deliberately for large images.

If a request is really asking to extract data for later analysis rather than display a chart, route to [conversion and I/O](../../conversion-and-io/SKILL.md) for export or `ee_to_*` guidance.

## 4. Palettes, legends, and colorbars

Use `geemap.colormaps` for palette generation and matplotlib colorbars; use `geemap.legends` for built-in thematic legend dictionaries; use map-specific `add_colorbar`/`add_legend` methods only after the target map backend is chosen.

```python
import geemap
from geemap import colormaps, legends

palette = colormaps.get_palette("viridis", n_class=5, hashtag=True)
vis_params = {"min": 0, "max": 1, "palette": palette}

# Local matplotlib figure, safe without EE credentials.
fig = colormaps.get_colorbar(palette, vmin=0, vmax=1, discrete=True, return_fig=True)

# Top-level geemap helper writes or returns a small colorbar image.
geemap.create_colorbar(width=150, height=30, palette=palette, labels=["low", "high"])

# Built-in dictionaries include names such as NLCD, ESA_WorldCover, Dynamic_World.
legend_dict = legends.builtin_legends["Dynamic_World"]
```

Validation rules:

- Normalize colors to `#RRGGBB` before passing them to UI widgets. `colormaps.get_palette(..., hashtag=True)` is the safest default.
- `get_palette` includes named extra palettes: `ndvi`, `ndwi`, `dem`, `dw`, and `esri_lulc`; all other names are looked up in matplotlib colormaps.
- For custom legends, label and color lists must be the same length; built-in legend keys must match `legends.builtin_legends` exactly.
- For map colorbars, set scalar `min` and `max`; use `discrete=True` only with a categorical palette.

## 5. Publication static maps with cartoee

`geemap.cartoee` creates cartopy/matplotlib maps. It is the correct backend for publication-style static figures when cartopy is installed.

```python
import ee
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from geemap import cartoee

ee.Initialize(project="your-ee-project")
image = ee.Image("USGS/SRTMGL1_003")
region = [-122.6, 37.0, -121.8, 37.7]
vis = {"min": 0, "max": 3000, "palette": cartoee.build_palette("terrain", 8)}

fig = plt.figure(figsize=(8, 6))
ax = cartoee.get_map(image, proj=ccrs.PlateCarree(), region=region, vis_params=vis)
cartoee.add_colorbar(ax, vis, loc="right", discrete=True, label="Elevation (m)")
cartoee.add_gridlines(ax, interval=0.25, linestyle="--", alpha=0.4)
cartoee.add_scale_bar_lite(ax, length=20, unit="km")
cartoee.add_north_arrow(ax)
cartoee.savefig(fig, "static-map.png", dpi=200)
```

Cartoee checks:

- Cartopy is optional; if it is absent, use palette/colorbar helpers as a fallback and install cartopy before static map rendering.
- `add_layer` accepts `ee.Image`, `ee.ImageCollection`, `ee.Geometry`, `ee.Feature`, or `ee.FeatureCollection`; non-images are styled then converted to an image.
- Always set a bounded `region` for deterministic thumbnails. If the default region yields a blank RGB visualization, pass an explicit rectangle and verify coordinate order visually.
- Do not provide both `cmap` and `vis_params["palette"]` to `add_layer`; source validation raises a key error.
- `add_colorbar` requires either `loc` (`left`, `right`, `bottom`, `top`) or a custom matplotlib `cax`.

## 6. Plotly charts and Plotly map backend

Use `geemap.plot` for fast Plotly Express figures from pandas data or CSV paths/URLs. Use `geemap.plotlymap.Map` when the output should be a Plotly map rather than an ipyleaflet/folium map.

```python
import pandas as pd
from geemap import plot
from geemap import plotlymap

summary = pd.DataFrame({"class": ["water", "trees"], "area": [14.2, 83.5]})
fig = plot.bar_chart(summary, x="class", y="area", title="Area by class", y_label="km²")
fig.show()

m = plotlymap.Map(center=(40, -100), zoom=3, basemap="open-street-map", ee_initialize=False)
m.add_tile_layer("TILE_URL/{z}/{x}/{y}.png", name="Tiles")
```

Plotly map notes:

- Constructor center is `(lat, lon)`, unlike MapLibre's `(lon, lat)` center.
- Set `ee_initialize=False` for local-only Plotly work or no-auth smoke tests.
- `add_controls`/`remove_controls` require a string or list of strings.
- `add_heatmap` accepts a pandas DataFrame or CSV path with latitude, longitude, and value columns.
- `fix_widget_error()` patches a known Plotly FigureWidget `mapbox._derived` error; use it only when that exact error appears.

## 7. Optional web visualization backends

### pydeck (`geemap.deck`)

```python
from geemap import deck

m = deck.Map(center=(40, -100), zoom=4, ee_initialize=False)
m.add_layer("TILE_URL/{z}/{x}/{y}.png", layer_name="tiles")
```

Use pydeck for deck.gl layers, custom tile layers, and GeoDataFrame/vector overlays when `pydeck` and needed vector extras are installed.

### kepler.gl (`geemap.kepler`)

```python
from geemap import kepler

m = kepler.Map(center=[40, -100], zoom=3, height=600, width=900)
m.add_df(summary, layer_name="summary")
html = m.to_html(filename="kepler.html", read_only=True)
```

Use kepler.gl for exploratory point/vector dashboards, config import/export, and Streamlit embedding when `keplergl` is installed. File readers may require `geopandas` and local/vector dependencies.

### MapLibre (`geemap.maplibregl`)

```python
import geemap.maplibregl as geemap_ml

m = geemap_ml.Map(center=(-100, 40), zoom=3, style="positron")
m.add_legend(title="Classes", legend_dict={"Water": "#419BDF", "Trees": "#397D49"})
m.add_colorbar(vis_params={"min": 0, "max": 1, "palette": ["#0000ff", "#00ff00"]})
```

Use MapLibre for ipywidget MapLibre GL maps, style layer editing, PMTiles, 3D terrain/buildings, and HTML/Streamlit output when `geemap[maplibre]` dependencies are installed. Its center is `(lon, lat)`. MapTiler styles and 3D terrain need a MapTiler key unless you use Carto or demo styles.

## Visual validation checklist

- Chart data: named columns/properties exist; x/y series lengths match; dates are parsed; EE collections are small or filtered.
- Reducers: image charts specify reducer, scale, and bounded region where required.
- Colors: palettes are valid hex strings; categorical palette length matches class count; use `hashtag=True` when UI widgets require CSS colors.
- Colorbars: `min < max`, opacity is numeric and within 0-1 for map layers, orientation is `horizontal` or `vertical`, and cartoee location is valid.
- Static maps: region is bounded; projection is cartopy-compatible; gridline/scale/north-arrow annotations do not cover the main data.
- Optional backends: confirm imports before promising output; provide a fallback such as local matplotlib colorbar, Plotly chart, or HTML-only export when a widget/backend is unavailable.
