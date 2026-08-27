# Clustering and NetworkCollection Reference

## Purpose

Read this when a task asks to reduce time resolution, aggregate buses, cluster a spatial network, or compare multiple scenario networks. Clustering changes network dimensions; prefer clustering before solving unless you explicitly understand how to discard or reinterpret solved outputs.

## Temporal clustering

Temporal clustering is available through `n.cluster.temporal` and module-level helpers. The accessor returns new networks and does not mutate the original network.

| Task | Accessor call | Full-result call | Key behavior |
| --- | --- | --- | --- |
| Resample to coarser periods | `n.cluster.temporal.resample("6h")` | `n.cluster.temporal.get_resample_result("6h")` | Aggregates snapshot weightings and dynamic attributes by pandas offset. Requires a `DatetimeIndex` unless investment periods are present. |
| Downsample | `n.cluster.temporal.downsample(4)` | `n.cluster.temporal.get_downsample_result(4)` | Keeps every fourth snapshot and scales snapshot weightings so total modeled hours are preserved. |
| Segment with TSAM | `n.cluster.temporal.segment(10)` | `n.cluster.temporal.get_segment_result(10)` | Uses optional `tsam`; creates variable-duration segments. |
| Apply custom map | `n.cluster.temporal.from_snapshot_map(snapshot_map)` | `n.cluster.temporal.get_from_snapshot_map_result(snapshot_map)` | Aggregates according to a user-supplied Series/DataFrame whose index matches `n.snapshots`. |

Full-result calls return a `TemporalClustering` object with:

- `.n`: the clustered network.
- `.snapshot_map`: a pandas `Series` mapping original snapshots to clustered snapshots.

### Temporal rules and caveats

- `resample` and `downsample` are base workflows and do not require `tsam`.
- `segment` requires `tsam`; if it is missing, use resample/downsample or install the optional package in an environment you control.
- `stride` for downsample must be at least 1.
- `segment(num_segments)` requires `1 <= num_segments <= len(n.snapshots)`.
- Temporal clustering does not yet support stochastic networks.
- TSAM segmentation does not support networks with investment periods.
- Applying temporal clustering after solving can make dispatch and storage state-of-charge outputs inconsistent; cluster first, then solve again.
- Default aggregation uses means for most dynamic attributes, `max` for lower bounds such as `e_min_pu`, and `min` for upper bounds such as `e_max_pu`; pass `aggregation_rules` to override.
- Leap-day handling is opt-in through `drop_leap_day=True` for resampling.

### Minimal temporal pattern

```python
result = n.cluster.temporal.get_resample_result("6h")
clustered = result.n
snapshot_map = result.snapshot_map
assert clustered.snapshot_weightings["objective"].sum() == n.snapshot_weightings["objective"].sum()
```

## Spatial clustering

Spatial clustering is available through `n.cluster.spatial`. The most robust workflow is to construct or inspect a busmap, then aggregate with `cluster_by_busmap`.

| Task | Accessor call | Optional dependency | Notes |
| --- | --- | --- | --- |
| Manual busmap aggregation | `n.cluster.spatial.cluster_by_busmap(busmap)` | None beyond base PyPSA stack | Best fallback when an algorithmic busmap is unavailable. |
| Full manual result | `n.cluster.spatial.get_clustering_from_busmap(busmap)` | None beyond base PyPSA stack | Returns clustered network plus busmap and linemap. |
| K-means busmap | `n.cluster.spatial.busmap_by_kmeans(weights, n_clusters=...)` | `scikit-learn` | Requires integer-like bus weights; PyPSA repeats coordinates by weight before K-means. |
| HAC busmap | `n.cluster.spatial.busmap_by_hac(n_clusters=..., feature=...)` | `scikit-learn` | Uses network adjacency and optional bus-indexed features. |
| Greedy modularity busmap | `n.cluster.spatial.busmap_by_greedy_modularity(n_clusters=...)` | Compatible NetworkX | Uses graph-community structure; does not require scikit-learn. |

### Manual busmap pattern

```python
import pandas as pd

busmap = pd.Series(
    {"north_1": "north", "north_2": "north", "south_1": "south"},
    name="busmap",
)
clustered = n.cluster.spatial.cluster_by_busmap(
    busmap,
    with_time=True,
    line_length_factor=1.0,
)
```

If you need the line mapping for post-processing, call `get_clustering_from_busmap` instead:

```python
clustering = n.cluster.spatial.get_clustering_from_busmap(busmap)
clustered = clustering.n
linemap = clustering.linemap
```

### Aggregation controls for `cluster_by_busmap`

| Parameter | Use |
| --- | --- |
| `with_time` | Keep and aggregate time-dependent attributes. Disable for a purely static clustered topology. |
| `line_length_factor` | Scale new line lengths after aggregating bus coordinates. |
| `aggregate_generators_weighted` | Aggregate generators by carrier using capacity-weighted strategies. |
| `aggregate_one_ports` | Dict/list-like selection of one-port components to aggregate explicitly. |
| `aggregate_generators_carriers` | Restrict generator carriers included in weighted generator aggregation. |
| `aggregate_generators_buses` | Restrict generator aggregation to selected buses. |
| `scale_link_capital_costs` | Scale link capital costs with changed link length. |
| `bus_strategies`, `one_port_strategies`, `generator_strategies`, `line_strategies` | Override default aggregation rules. |
| `custom_line_groupers` | Prevent lines with different grouping attributes, such as build year, from being merged. |

### Spatial caveats

- A busmap must cover every old bus you expect to preserve; unmapped buses can drop attached components.
- K-means ignores branch topology; use HAC, greedy modularity, or manual busmaps when topology matters.
- HAC without a feature treats buses as equally similar apart from network connectivity.
- Multi-port links are remapped across every available bus port; inspect clustered links when using sector-coupled networks.
- Clustered networks should usually be solved again; old dispatch on the original network does not automatically become valid for the clustered network.

## NetworkCollection comparison

`pypsa.NetworkCollection` stores references to multiple networks and exposes many data accessors plus `.statistics`. It is useful for scenario comparison, especially when each scenario was solved separately.

```python
import pandas as pd
import pypsa

nc = pypsa.NetworkCollection(
    [base_network, variant_network],
    index=pd.Index(["base", "variant"], name="scenario"),
)

balance = nc.statistics.energy_balance()
variant_balance = balance.xs("variant", level="scenario")
```

### Construction rules

- Pass a list, dict, pandas Series, or paths accepted by `pypsa.Network`.
- If no index is provided, PyPSA derives it from network names; duplicate names require an explicit index.
- Every MultiIndex level must be named.
- The collection contains references, not copies; mutating an original network mutates the collection view.
- Mixing networks with and without investment periods is rejected.

### Dimension-alignment strategy

| Situation | Recommended action |
| --- | --- |
| Same topology and same snapshots | Use collection statistics and plots directly; facet or group by the collection index. |
| Same topology but different snapshot calendars | Compare time-aggregated statistics such as `energy_balance()` or `installed_capacity()` first; avoid raw time-series joins unless you align calendars explicitly. |
| Different component names or clustered topologies | Compare at higher-level groupers such as `carrier`, `bus_carrier`, `country`, or a custom grouper rather than component `name`. |
| Different investment-period state | Normalize periods before collection construction; do not mix period and non-period networks. |
| Stochastic and non-stochastic scenarios | Treat as an alignment-risk area; aggregate to comparable dimensions or compare separately. |

For plots, collection index levels can become colors or facets. If automatic layout is unreadable, pass `facet_col`, `facet_row`, `color`, and explicit orders. See [plotting-reference.md](plotting-reference.md).

## Smoke-test helper

Run [../scripts/pypsa_clustering_smoke.py](../scripts/pypsa_clustering_smoke.py) to validate base temporal clustering and a safe busmap aggregation. The optional scikit-learn and TSAM sections skip cleanly when those packages are missing.
