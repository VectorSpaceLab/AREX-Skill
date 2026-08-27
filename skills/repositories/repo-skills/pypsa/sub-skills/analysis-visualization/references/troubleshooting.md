# Analysis and Visualization Troubleshooting

## Purpose

Read this when PyPSA statistics are empty, plots fail in headless runs, optional clustering dependencies are unavailable, or scenario comparisons do not align.

## Quick triage

1. Decide whether the network is solved. Use `installed_capacity` or `installed_capex` before solving; use dispatch, price, cost, and balance metrics after solving.
2. Compute the statistic before plotting it. Inspect `result.empty`, `result.index.names`, and `result.head()`.
3. For static plots in non-interactive sessions, use an off-screen Matplotlib backend and `geomap=False`.
4. For collection comparisons, compare each scenario slice with `.xs(label, level="scenario")` before making a combined plot.
5. Run [../scripts/pypsa_analysis_smoke.py](../scripts/pypsa_analysis_smoke.py) or [../scripts/pypsa_clustering_smoke.py](../scripts/pypsa_clustering_smoke.py) to separate package/runtime issues from user-network issues.

## Troubleshooting matrix

| Symptom or error fragment | Likely cause | What to do next |
| --- | --- | --- |
| `Series([], dtype=...)`, empty `DataFrame`, or blank statistic for `optimal_capacity`, `capex`, `opex`, `prices`, `energy_balance`, `revenue`, or `market_value` | Network has not been optimized or solved, or solve outputs were cleared. | Use `installed_capacity` / `installed_capex` for input-side analysis, or solve the network and re-run the metric. |
| `installed_capacity` is non-empty but `optimal_capacity` is empty | Expected on an unsolved network. | Report both facts explicitly; do not treat the empty optimized metric as proof of missing components. |
| Time-varying statistic contains NaNs before solve | Dispatch/price time series have not been populated. | Solve first, or use static/input-side metrics. If preserving time, pass `groupby_time=False` only after the relevant dynamic outputs exist. |
| Result disappears after plotting or filtering | Plot method forwarded filters such as `carrier`, `bus_carrier`, `components`, or `query` and no rows matched. | Re-run the underlying statistic without filters, then add filters one by one. Use `drop_zero=False` while debugging. |
| `KeyError` for a grouper name | The name is not a built-in grouper and is not a component static column. | Use a built-in grouper (`carrier`, `bus_carrier`, `bus`, `country`, `location`, `name`, `unit`), add the missing static column, or register a custom grouper. |
| `prices` plot rejects `carrier` | Prices are bus-based, not component-carrier based. | Filter prices with `bus_carrier`, or group by bus attributes such as `country` or `name`. |
| Statistics map says prices are not implemented | `prices` cannot be plotted with `statistics.<metric>.plot.map`. | Use a bar/line/box/histogram prices chart, or plot bus values manually through `n.plot.map` after deriving a bus-indexed series. |
| `ConsistencyError` or missing carrier-color plot failure | Carrier colors are absent or inconsistent. | Define carrier rows with `color` values before plotting; use exact carrier ids when `nice_names=False`. |
| Matplotlib backend or display error | A GUI backend is being used in a headless session. | Set `MPLBACKEND=Agg` or call `matplotlib.use("Agg", force=True)` before importing `pyplot`. |
| Cartopy missing, warning about non-geographic fallback, or `GeoAxesSubplot` error | `geomap=True` needs Cartopy and a Cartopy GeoAxes when passing `ax`. | Use `geomap=False` for smoke/debug plots; when using Cartopy, create the axis with a Cartopy projection. |
| Static map uses the wrong flow or no flow arrows | `line_flow`, `link_flow`, or `transformer_flow` points to missing solved flow data or wrong indexes. | Solve first, then pass a snapshot label, `"mean"`, a callable, scalar, or a correctly indexed branch `Series`. |
| `n.plot.explore` fails with missing `pydeck` | Pydeck interactive map stack is optional. | Skip the Pydeck map, install pydeck in a controlled environment, or use `n.plot.map(geomap=False)` / `n.plot.iplot(iplot=False)`. |
| Plotly figure exists but nothing displays | Interactive figure was built in a non-notebook/non-browser context. | Treat the returned object as the result; write or show it only when a user explicitly wants a file/browser artifact. |
| Mapbox token or style error from `n.plot.iplot(mapbox=True)` | Token-requiring Mapbox style was selected without credentials. | Use `mapbox=False` or an open style; avoid token-requiring styles in automated runs. |
| `Optional dependency 'sklearn' not found` | K-means/HAC spatial clustering requires scikit-learn. | Use a manual busmap with `cluster_by_busmap`, or install scikit-learn if algorithmic spatial clustering is required. |
| `Optional dependency 'tsam' not found` | Temporal segmentation requires TSAM. | Use `resample` or `downsample` for base temporal clustering, or install TSAM before calling `segment`. |
| Temporal clustering raises `stochastic networks` | Temporal clustering does not support stochastic networks. | Reduce/aggregate scenarios separately or choose a different comparison plan. |
| `segment()` raises about investment periods | TSAM segmentation does not support investment-period networks. | Use resample/downsample within periods or segment a non-period network. |
| Warning about clustering a solved network | Temporal clustering after solving can invalidate dispatch and storage outputs. | Cluster first, discard old result tables, then solve the clustered network again. |
| `snapshot_map index must match network snapshots` | Custom temporal map has the wrong index. | Reindex the map to exactly `n.snapshots` before `from_snapshot_map`. |
| `NetworkCollection` duplicate names error | No explicit index was provided and network names are duplicated. | Pass a named pandas Index or MultiIndex. |
| `All levels of MultiIndex must have names` | Collection MultiIndex has unnamed levels. | Set names such as `scenario`, `year`, and `policy` before constructing the collection. |
| Collection rejects mixed investment-period networks | Some member networks have periods and others do not. | Normalize period structure before comparison, or compare those networks separately. |
| Collection statistics or plots look misaligned | Raw snapshots, component names, scenarios, or periods differ. | Compare time-aggregated metrics first; group by common dimensions such as `carrier` or `bus_carrier`; align raw time series only when necessary. |
| Plot is unreadable for a large network | Too many components, carriers, buses, snapshots, or collection scenarios are rendered at once. | Filter, aggregate, facet, use `col_wrap`, reduce marker/branch sizes, and prefer maps with pre-scaled series. |

## Unsolved-network workflow

```python
# Good before solving
installed = n.statistics.installed_capacity(groupby="carrier", drop_zero=False)

# Expected to be empty before solving
optimized = n.statistics.optimal_capacity(drop_zero=False)

if optimized.empty:
    print("The network has no solved optimized-capacity results yet.")
```

For an analysis report, keep the distinction explicit: "input-side capacity exists, but solve-dependent outputs are unavailable." Do not invent dispatch, prices, or optimized capacity values.

## Collection alignment workflow

```python
balance = nc.statistics.energy_balance()
for scenario in nc.index:
    one = balance.xs(scenario, level=nc.index.name or "network")
    print(scenario, one.sum())
```

If the collection index is a MultiIndex, slice by the named level you need. If component names differ across scenarios, compare by `carrier`, `bus_carrier`, `country`, or a custom grouper instead of component name.

## Plot readability workflow

```python
stat = n.statistics.energy_balance(bus_carrier="AC", groupby=["carrier", "bus_carrier"])
fig, ax, grid = n.statistics.energy_balance.plot.bar(
    bus_carrier="AC",
    color="carrier",
    col_wrap=2,
)
```

Before plotting all data, prototype with a small filter and inspect the statistic. For maps, choose `geomap=False` while debugging; enable Cartopy only after the data and sizing are correct.
