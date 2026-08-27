---
name: mobility-and-transport
description: "Build spatial OD mobility graphs and local GTFS/GBFS
  transportation graphs with explicit schemas, service windows, time semantics,
  and DuckDB spatial prerequisites."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 3-Clause
---

# Mobility and transport

Use this skill when the task is to turn an existing origin-destination (OD)
data set, a local GTFS schedule archive, or a local GBFS JSON directory into
city2graph graph data. The package is GeoDataFrame-first: prefer returning
`(nodes_gdf, edges_gdf)` and convert that pair with `city2graph.utils.gdf_to_nx`
only when a NetworkX consumer explicitly requires it.

This skill covers:

- `city2graph.mobility.od_matrix_to_graph` for OD edge lists and adjacency
  matrices/arrays;
- `city2graph.transportation.load_gtfs` and `load_gbfs` for local feed
  ingestion;
- `get_od_pairs` for dated, stop-to-stop GTFS legs; and
- `travel_summary_graph` for an aggregated stop-level service graph.

It does **not** download feeds, query a live transit API, geocode locations, or
construct a road-routing network. All workflows can be exercised with local
files or an in-memory DuckDB connection. A local/cached DuckDB `spatial`
extension is still required for geometry-producing transit workflows; a first
attempt to `INSTALL spatial` can itself require package access, so do not claim
an offline environment is ready until that extension is available.

## Choose the workflow

| Starting data | Entry point | Result |
|---|---|---|
| Edge-list OD flows plus zone geometries | `od_matrix_to_graph(..., matrix_type="edgelist")` | Spatial zone nodes and weighted OD edges |
| Labeled adjacency DataFrame | `od_matrix_to_graph(..., matrix_type="adjacency")` | Spatial zone nodes and non-zero adjacency edges |
| NumPy adjacency array | Same, with `matrix_type="adjacency"` | Array rows/columns mapped to zone order |
| Local `.zip` GTFS schedule | `load_gtfs(path)` | In-memory DuckDB tables |
| GTFS connection and individual legs needed | `get_od_pairs(con, ...)` | One row per consecutive stop leg/date |
| GTFS connection and an aggregate network needed | `travel_summary_graph(con, ...)` | Stop nodes and service-weighted summary edges |
| Local GBFS JSON directory | `load_gbfs(path)` | In-memory DuckDB tables; no transit summary is inferred |

Do not treat GBFS station/bike/vehicle tables as GTFS `stops`, `trips`, or
`stop_times`; `load_gbfs` is an ingestion primitive, not a graph builder.

## Public API and defaults

The installed package exposes these functions both from their modules and via
the package-level re-export:

```python
from city2graph.mobility import od_matrix_to_graph
from city2graph.transportation import (
    get_od_pairs,
    load_gbfs,
    load_gtfs,
    travel_summary_graph,
)
```

Important defaults:

- `od_matrix_to_graph`: `matrix_type="edgelist"`, `source_col="source"`,
  `target_col="target"`, `directed=True`, `include_self_loops=False`,
  `compute_edge_geometry=True`, and GeoDataFrame output.
- `get_od_pairs`: `include_geometry=True`, `directed=False`.
- `travel_summary_graph`: no time/date bounds, `directed=False`,
  `use_frequencies=True`, and GeoDataFrame output.
- `load_gtfs` accepts a local path to a ZIP archive; `load_gbfs` accepts a local
  directory and recursively reads `*.json` files.

The exact signatures are kept in the bundled workflow references. If a caller
passes `as_nx`, emit/expect the package deprecation warning: `as_nx` is a
legacy compatibility path and is not the recommended interface.

## Fast operating procedure

1. **Classify the source.** Decide whether the input is an OD table/matrix,
   GTFS ZIP, or GBFS directory. Do not silently reinterpret a GBFS feed as
   GTFS.
2. **Check prerequisites before calling.** Confirm identifiers, geometry/CRS,
   feed tables, service dates, stop times, and the DuckDB spatial extension as
   applicable. See `references/troubleshooting.md`.
3. **Use the GeoDataFrame output first.** Inspect row counts, indices, columns,
   CRS, edge direction, and empty-edge behavior before converting to another
   graph representation.
4. **Make filtering explicit.** Record threshold and self-loop policy for OD;
   record date/time windows and `use_frequencies` for transit.
5. **Validate invariants.** For OD, confirm every retained endpoint belongs to
   the zone set. For transit, confirm positive travel times/frequencies and
   that the requested calendar/time window actually selects service.
6. **Keep provenance with the result.** Record local input paths, feed table
   names, zone/stop ID columns, CRS, parameters, and warnings. No live-network
   provenance is expected because this skill never fetches data.

# Bundled references

- [OD workflows and schemas](references/od-workflows.md)
- [GTFS/GBFS workflows and service semantics](references/transit-workflows.md)
- [Troubleshooting and validation](references/troubleshooting.md)

## Minimal acceptance checklist

Before handing a graph to a downstream analysis:

- [ ] The input type and identifier mapping are documented.
- [ ] OD zones have unique, non-null IDs; adjacency labels or array ordering
      have been checked against those zones.
- [ ] The returned edge index is understood (`source,target` for OD and
      `from_stop_id,to_stop_id` for summary transit edges).
- [ ] Thresholds are inclusive when supplied and the no-threshold positive-only
      rule is intentional.
- [ ] Direction and reciprocal-edge behavior are intentional.
- [ ] Geometry CRS is present or the missing/geographic CRS warning is accepted.
- [ ] GTFS has the required tables for the selected operation and valid local
      stop geometry or coordinates for geometry output.
- [ ] GTFS date strings are `YYYYMMDD` and time strings are `HH:MM:SS`,
      including extended hours such as `25:30:00` where appropriate.
- [ ] DuckDB spatial support is loaded and the local environment does not rely
      on an unapproved live-network download.
- [ ] Any `as_nx` warning is treated as migration work, not suppressed as a
      durable API choice.
