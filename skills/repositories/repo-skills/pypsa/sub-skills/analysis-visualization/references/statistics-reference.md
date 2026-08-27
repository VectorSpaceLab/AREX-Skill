# PyPSA Statistics Reference

## Purpose

Read this when a task asks for PyPSA metrics, filtering, grouping, custom groupers, or statistics-based comparison across networks. The public accessors are `n.statistics` and the alias `n.stats`.

## Accessor pattern

```python
# Same accessor, two names
assert n.stats is n.statistics

installed = n.statistics.installed_capacity(groupby="carrier")
balance = n.stats.energy_balance(bus_carrier="AC")
summary = n.statistics(components=["Generator", "Line"], groupby=["carrier", "bus_carrier"])
```

Statistics methods return pandas `Series` or `DataFrame` objects with component and grouping levels in the index. Use pandas indexing after the statistic call for downstream reshaping, or pass PyPSA filters directly to avoid calculating unnecessary rows.

## Metric catalog and solved-data expectations

| Metric | Typical purpose | Use before solving? | Notes |
| --- | --- | --- | --- |
| `installed_capacity` | Static installed capacities before optimization. | Yes | Best first check on unsolved networks. |
| `installed_capex` | Static installed capacity multiplied by capital cost. | Yes | Uses built capacities, not optimization expansion. |
| `optimal_capacity` | Capacities after optimization. | No | Empty on unsolved networks; populated from optimized `*_nom_opt` values. |
| `expanded_capacity` | Difference between optimal and installed capacity. | No | Meaningful only after optimization with capacity variables/results. |
| `capex` | Capital expenditure based on optimized capacities. | No | Uses optimized capacities and cost attributes. |
| `expanded_capex` | Capital expenditure of expanded capacity. | No | Difference between optimized and installed-capex terms. |
| `overnight_cost` | Overnight investment cost based on optimized capacities. | No | Uses optimized capacities. |
| `fom` | Fixed O&M based on optimized capacities. | No | Uses optimized capacities and `fom_cost`. |
| `opex` | Operational expenditure. | No | Requires dispatch/storage outputs; supports cost-type variants where available. |
| `supply` / `withdrawal` | Energy supplied or withdrawn by components. | No | Use `groupby_time=False` for snapshot-level time series. |
| `energy_balance` | Supply minus withdrawal by carrier/bus carrier. | No | Positive values are supply, negative values are withdrawal. |
| `transmission` | Transmission between buses of the same carrier. | No | Often useful with `bus_carrier`. |
| `curtailment` | Curtailed energy. | No | Requires dispatch and availability time series. |
| `capacity_factor` | Utilization/capacity factor. | No | Snapshot-level views are useful for distribution plots. |
| `revenue` / `market_value` | Revenue and market-value summaries. | No | Requires prices and dispatch. |
| `prices` | Marginal prices at buses. | No | Filter by `bus_carrier`; do not use `carrier` for prices plots. |
| `system_cost` | Total system cost. | No | Combines capex/FOM/OPEX terms; `groupby_time=False` is not a real time series. |

If a solve-dependent metric returns an empty `Series`, an empty `DataFrame`, or all-NaN time series on an unsolved network, that is expected. Use `installed_capacity` or `installed_capex` for input-side analysis, or solve the network before interpreting result metrics.

## Common parameters

| Parameter | Use | Notes |
| --- | --- | --- |
| `components` | Limit component types, for example `"Generator"` or `["Generator", "Line"]`. | If omitted, PyPSA considers eligible one-port and branch components. |
| `carrier` | Filter by component carrier. | Accepts a string or sequence. With nice names enabled, filters may be normalized to nice carrier labels. |
| `bus_carrier` | Filter by carrier of connected buses. | When set, PyPSA considers all relevant ports by default. |
| `at_port` | Select ports for multi-port components. | Use `"all"`, `0`, `"1"`, or a list as appropriate. |
| `groupby` | Group rows. | Built-ins include `carrier`, `bus_carrier`, `bus`, `country`, `location`, `name`, and `unit`; direct component-static columns can also be used. |
| `groupby_method` | Aggregate groups, usually `"sum"`, `"mean"`, or another pandas reducer. | Applies to component grouping, not time aggregation. |
| `groupby_time` | Aggregate time-varying values. | `"sum"` and `"mean"` account for snapshot weightings; `False` preserves the time axis. |
| `nice_names` | Replace carrier names by carrier `nice_name` values. | Disable with `nice_names=False` when exact carrier ids are needed. |
| `drop_zero` | Remove zero rows. | If a diagnostic needs to prove a metric is zero, pass `drop_zero=False`. |
| `round` | Round numeric output. | Pass `round=None` for exact numerical comparisons. |
| `aggregate_across_components` | Collapse identical grouping labels across component classes. | Deprecated in favor of explicit pandas aggregation on the returned result. |

## Built-in groupers

Use strings directly for most tasks:

```python
n.statistics.installed_capacity(groupby="carrier")
n.statistics.energy_balance(groupby=["carrier", "bus_carrier"])
n.statistics.prices(groupby=["name", "country"], groupby_time=False)
```

For explicit grouper functions or mixed string/function usage:

```python
from pypsa.statistics import groupers

n.statistics.energy_balance(groupby=groupers[["carrier", "bus_carrier"]])
n.statistics.installed_capacity(groupby=["carrier", groupers.bus_carrier])
```

Important grouper behavior:

- `bus_carrier`, `bus`, `country`, `location`, and `unit` map component bus references to bus table attributes.
- `name` groups by component names and is useful for debugging individual assets.
- For multi-port components, pass `at_port` or `bus_carrier` intentionally so the relevant side of a Link/Process is counted.
- If a built-in grouper name is not found, PyPSA attempts to use a component static column with that name; unknown names raise a key error.

## Custom groupers

Register a custom grouper when a reusable grouping rule is clearer than repeated pandas code.

```python
import pypsa


def voltage_level(n, c, port="", nice_names=False):
    bus_column = f"bus{port}"
    buses = n.c[c].static[bus_column]
    return buses.map(n.c.buses.static.v_nom).rename("voltage")

pypsa.statistics.groupers.add_grouper("voltage", voltage_level)
by_voltage = n.statistics.installed_capacity(groupby="voltage")
```

A custom grouper should accept at least `(n, c)` and, when relevant, `port` and `nice_names`. It must return a pandas `Series` aligned to the component index.

## Time aggregation patterns

```python
# Weighted total across all snapshots
n.statistics.energy_balance(groupby_time="sum")

# Weighted mean by time
n.statistics.supply(groupby_time="mean")

# Preserve snapshot columns or rows for plotting/diagnostics
full_ts = n.statistics.supply(groupby_time=False)
```

Use `groupby_time=False` for line, area, box, violin, and histogram diagnostics that need time variation. Use aggregated values for scenario comparison when networks have different snapshot calendars.

## NetworkCollection statistics

`pypsa.NetworkCollection` exposes `.statistics` like a network. Collection index levels become leading levels in statistic outputs.

```python
import pandas as pd
import pypsa

nc = pypsa.NetworkCollection(
    [base_network, variant_network],
    index=pd.Index(["base", "variant"], name="scenario"),
)

balance = nc.statistics.energy_balance()
base_balance = balance.xs("base", level="scenario")
```

Use collection statistics for scenario comparisons, but read [clustering-collections.md](clustering-collections.md) before comparing raw time-series dimensions or mixed investment-period/stochastic networks.

## Validation checklist

- Verify whether the network is solved before interpreting solve-dependent metrics.
- Use `drop_zero=False` when diagnosing zero versus missing data.
- Set `nice_names=False` when exact component or carrier ids matter.
- Confirm the returned index levels before joining with external data.
- For visual output, read [plotting-reference.md](plotting-reference.md); for empty or misleading metrics, read [troubleshooting.md](troubleshooting.md).
