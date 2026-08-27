# PyPSA Plotting Reference

## Purpose

Read this when a task asks for charts, maps, headless plotting, interactive figures, or readability choices for large PyPSA networks. Use [statistics-reference.md](statistics-reference.md) first when the plot data itself is unclear.

## Headless-safe setup

For scripts, CI, remote shells, or batch runs, configure Matplotlib before importing `pyplot`:

```python
import matplotlib
matplotlib.use("Agg", force=True)
import matplotlib.pyplot as plt
```

Use `geomap=False` for smoke tests and non-geographic debugging. `geomap=True` requires Cartopy and may need local map-feature data, so it is not the safe default.

## Statistics charts

Every statistic handler has `.plot` for static Matplotlib/Seaborn output and `.iplot` for Plotly output.

```python
# Static chart: returns figure, axes, and a FacetGrid-like object.
fig, ax, grid = n.statistics.energy_balance.plot.area(bus_carrier="AC")
plt.close(fig)

# Interactive chart: returns a Plotly figure object.
fig = n.statistics.installed_capacity.iplot.bar(components="Generator")
```

Available static and interactive chart types:

| Plot type | Static call | Interactive call | Typical use |
| --- | --- | --- | --- |
| Default | `n.statistics.<metric>.plot()` | `n.statistics.<metric>.iplot()` | Let PyPSA choose the metric-specific default. |
| Area | `.plot.area()` | `.iplot.area()` | Time-varying balances or supply. |
| Bar | `.plot.bar()` | `.iplot.bar()` | Aggregated capacities, costs, balances, or collection comparisons. |
| Line | `.plot.line()` | `.iplot.line()` | Snapshot-level series. |
| Scatter | `.plot.scatter()` | `.iplot.scatter()` | Exploratory relationships. |
| Box | `.plot.box()` | `.iplot.box()` | Distributions over snapshots or names. |
| Violin | `.plot.violin()` | `.iplot.violin()` | Distribution shape. |
| Histogram | `.plot.histogram()` | `.iplot.histogram()` | Frequency distributions. |
| Statistics map | `.plot.map()` | Not mirrored by `.iplot` | Geographic/statistical map via Matplotlib/Cartopy. |

Most statistics filters can be passed directly to plot calls: `components`, `carrier`, `bus_carrier`, `storage`, `at_port`, `nice_names`, `drop_zero`, and `round` when the underlying metric supports them. Use plot-level controls such as `x`, `y`, `color`, `facet_col`, `facet_row`, `query`, `row_order`, `col_order`, `col_wrap`, `height`, and `aspect` to make plots readable.

### Statistics map plots

```python
fig, ax = n.statistics.installed_capacity.plot.map(
    components="Generator",
    bus_carrier="AC",
    geomap=False,
)
plt.close(fig)
```

Map-plot notes:

- `prices` cannot be plotted on a statistics map.
- `energy_balance`, `supply`, and `withdrawal` can use transmission-flow arrows; defaults depend on the metric.
- `bus_area_fraction`, `branch_area_fraction`, and `flow_area_fraction` control size scaling.
- `bus_split_circle=True` separates positive and negative bus contributions.
- Carrier colors are used for legends and pies; define carrier `color` values before plotting.

## Network maps

### Static network map: `n.plot.map`

`n.plot` and `n.plot.map` are aliases for static network-map rendering. The call returns a dictionary of Matplotlib collections keyed by nodes, branches, and flows.

```python
fig, ax = plt.subplots()
collections = n.plot.map(
    ax=ax,
    geomap=False,
    line_flow="mean",
    bus_size=0.02,
)
plt.close(fig)
```

Useful arguments:

- `geomap=False` avoids Cartopy and works in headless smoke tests.
- `geomap=True`, `projection`, and `geomap_resolution` use Cartopy map features.
- If you pass `ax` with `geomap=True`, the axis must be a Cartopy GeoAxes; a normal Matplotlib axis is valid only with `geomap=False`.
- `bus_size` may be scalar, bus-indexed `Series`, or a MultiIndex `Series` with bus as the first level for pie charts.
- `bus_split_circle=True` splits positive and negative MultiIndex bus sizes into semicircles.
- `line_flow`, `link_flow`, and `transformer_flow` accept a snapshot label, aggregation string such as `"mean"`, a callable, scalar, or a correctly indexed `Series`.
- `geometry=True` uses WKT line geometry columns when present.

### Plotly network map: `n.plot.iplot`

Use `n.plot.iplot(iplot=False)` to build a Plotly-style figure dictionary without displaying it.

```python
fig_dict = n.plot.iplot(iplot=False, mapbox=False, title="Scenario network")
```

Plotly map notes:

- `mapbox=False` uses ordinary Plotly scatter/shapes and does not need map tiles or a token.
- `mapbox=True` can use Mapbox layouts. Token-requiring styles need an explicit token; avoid this in unattended runs.
- Use `line_text`, `link_text`, `bus_text`, and component-width/color series for richer hover information.

### Pydeck network map: `n.plot.explore` / `n.explore`

`n.plot.explore()` and `n.explore()` build an interactive Pydeck `Deck` object.

```python
deck = n.plot.explore(
    map_style="light",
    bus_size=25,
    tooltip=False,
)
```

Pydeck notes:

- Requires the optional `pydeck` stack at runtime.
- Valid map styles include light/dark/road/no-label variants and `none`.
- `bus_columns`, `line_columns`, `link_columns`, and `transformer_columns` select tooltip columns; missing columns are skipped with a warning.
- `auto_scale=True` helps large networks by scaling sizes to configured maxima.
- Coordinates should be valid WGS84 longitude/latitude values for Pydeck; invalid buses are dropped from the map.

## NetworkCollection plotting

`NetworkCollection.statistics.<metric>.plot` and `.iplot` support collection outputs. Collection index levels become plot dimensions.

```python
fig, ax, grid = nc.statistics.installed_capacity.plot.bar(
    components="Generator",
    facet_col="scenario",
)
plt.close(fig)
```

For single-index collections, bar plots often group by the collection index. For MultiIndex collections or multi-investment networks, PyPSA may facet by one or more dimensions. When automatic layout is hard to read, pass `facet_col`, `facet_row`, `color`, `col_wrap`, and explicit ordering values.

## Readability strategy for large networks

1. Compute the statistic first and inspect its index levels.
2. Filter with `components`, `carrier`, `bus_carrier`, or `query` before plotting.
3. Aggregate with `groupby=["carrier", "country"]`, `groupby=["carrier", "bus_carrier"]`, or a custom grouper.
4. Use `drop_zero=True`, `round=2`, and `nice_names=False` only when those choices match the analysis.
5. For maps, reduce marker/branch size with area fractions or pass pre-scaled `Series` values.
6. For collections, facet by scenario or year rather than stacking many scenarios on one axis.

## Smoke-test helper

Run [../scripts/pypsa_analysis_smoke.py](../scripts/pypsa_analysis_smoke.py) to check headless statistics charts, maps, Plotly figures, optional Pydeck construction, and collection comparison on a tiny self-contained network.
