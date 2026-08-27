# Analysis reference

This sub-skill covers street-network statistics, bearings, and orientation entropy.

## Street statistics overview

Use the helpers in `osmnx.stats` when you want counts, densities, or average network measures rather than a single route.

| Function | Signature | Notes |
| --- | --- | --- |
| `stats.streets_per_node` | `(G)` | Reads the cached `street_count` node attribute. |
| `stats.streets_per_node_avg` | `(G)` | Average number of streets per node. |
| `stats.streets_per_node_counts` | `(G)` | Frequency table of street counts. |
| `stats.streets_per_node_proportions` | `(G)` | Street-count proportions. |
| `stats.intersection_count` | `(G, *, min_streets=2)` | Counts nodes with at least `min_streets` incident streets. |
| `stats.street_segment_count` | `(Gu)` | Counts undirected street segments. |
| `stats.street_length_total` | `(Gu)` | Total undirected street length. |
| `stats.edge_length_total` | `(G)` | Total directed edge length. |
| `stats.self_loop_proportion` | `(Gu)` | Fraction of edges that are self-loops. |
| `stats.circuity_avg` | `(Gu)` | Average street circuity; returns `None` if the straight-line denominator is zero. |
| `stats.count_streets_per_node` | `(G, *, nodes=None)` | Recomputes `street_count` from graph topology. |
| `stats.basic_stats` | `(G, *, area=None, clean_int_tol=None)` | Collects the standard summary dictionary. |

## What `basic_stats` returns

The returned dictionary always includes:

- `n`
- `m`
- `k_avg`
- `edge_length_total`
- `edge_length_avg`
- `streets_per_node_avg`
- `streets_per_node_counts`
- `streets_per_node_proportions`
- `intersection_count`
- `street_length_total`
- `street_segment_count`
- `street_length_avg`
- `circuity_avg`
- `self_loop_proportion`

It additionally includes:

- `node_density_km`, `intersection_density_km`, `edge_density_km`, `street_density_km` when `area` is provided.
- `clean_intersection_count` when `clean_int_tol` is provided.
- `clean_intersection_density_km` when both `area` and `clean_int_tol` are provided.

## Directed vs undirected usage

- `basic_stats` internally converts the graph to an undirected view for the street-level metrics.
- `street_segment_count`, `street_length_total`, `self_loop_proportion`, and `circuity_avg` should be interpreted on an undirected graph.
- `edge_length_total` is the directed total and will usually be larger than `street_length_total` on a two-way street network.
- If you manually build a graph, set `street_count` before calling `basic_stats` or `streets_per_node`.

## Bearing and orientation workflow

### `bearing.add_edge_bearings`

- Requires an **unprojected** graph.
- Writes a `bearing` edge attribute to all non-self-loop directed edges.
- Bearings are clockwise degrees from north.
- Self-loops are ignored because their bearings are undefined.

### `bearing.orientation_entropy`

- Signature: `(G, *, num_bins=36, min_length=0, weight=None)`.
- Requires `scipy`.
- Works on either `MultiGraph` or `MultiDiGraph`.
- On a `MultiGraph`, bearings are treated bidirectionally.
- On a `MultiDiGraph`, bearings are treated directionally.
- `weight` can be a numeric edge attribute such as `length`.
- `min_length` helps suppress noise from very short edges.

## Practical analysis recipe

1. Make sure the graph already has `street_count` on every node.
2. Call `basic_stats` for a compact summary.
3. Call `add_edge_bearings` on the unprojected graph if you need orientation measures.
4. Convert to an undirected graph when you want street-level orientation counts rather than direction-specific bearings.
5. Pass a numeric `weight` to `orientation_entropy` only after the graph has edge bearings.

## Common interpretation notes

- A high `k_avg` usually means many more directed edges per node.
- `circuity_avg` close to 1 means routes are close to straight-line geometry.
- `street_length_total` and `edge_length_total` differ because the former avoids double-counting bidirectional streets.
- `orientation_entropy` is sensitive to bin count, short edges, and whether you weight by length.
