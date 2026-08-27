---
name: osmnx
description: "Route OSMnx questions about OpenStreetMap data acquisition, graph
  modeling and file I/O, routing and network analysis, elevation, and static
  visualization."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# OSMnx

Use this repo skill when a task is about the `osmnx` package. The package helps you download, model, analyze, and visualize street networks and other OpenStreetMap features.

## Read first

- `references/package-overview.md` for the module map, public surface, and optional extras.
- `references/troubleshooting.md` for cross-cutting install/import, optional dependency, and service-limit failures.
- `references/repo-provenance.md` when you need to check whether this skill still matches the current checkout.
- `scripts/check_osmnx_environment.py --help` for the bundled environment diagnostic.

## Install and check

- Install the package itself with `python -m pip install osmnx`.
- If you are working from a local checkout, install it in editable mode with `python -m pip install -e .`.
- To cover the optional workflows used by this skill, install the relevant extras: `neighbors` for nearest-node/edge search, `entropy` for orientation entropy, `raster` for raster elevation, and `visualization` for static plots.
- Minimal import check: `python -I -c "import osmnx as ox; print(ox.__version__)"`
- Broader environment check: `python scripts/check_osmnx_environment.py`

OSMnx does not expose a general end-user CLI. Use Python imports and the bundled scripts in this skill instead.

## Route map

### `data-acquisition`
Use this when the user wants to fetch OSM data or plan a query.

Covers:
- `geocode`, `geocode_to_gdf`
- `graph_from_bbox`, `graph_from_point`, `graph_from_address`, `graph_from_place`, `graph_from_polygon`, `graph_from_xml`
- `features_from_bbox`, `features_from_point`, `features_from_address`, `features_from_place`, `features_from_polygon`, `features_from_xml`
- Nominatim/Overpass settings, cache behavior, rate limits, historical snapshots, custom filters, tags, and local OSM XML fallback

Read `sub-skills/data-acquisition/SKILL.md` for query planning and service-limit troubleshooting.

### `graph-modeling-io`
Use this when the user already has a graph or GeoDataFrames and needs validation, conversion, projection, simplification, truncation, or persistence.

Covers:
- graph and GeoDataFrame validation
- graph/GeoDataFrame conversion
- projection helpers
- simplification, intersection consolidation, truncation, and component selection
- GraphML, GeoPackage, and OSM XML save/load

Read `sub-skills/graph-modeling-io/SKILL.md` for data-model invariants and file-format rules.

### `routing-analysis`
Use this when the user wants nearest-node/edge matching, route solving, route GeoDataFrames, speeds, travel times, statistics, bearings, or orientation entropy.

Covers:
- `nearest_nodes`, `nearest_edges`
- distance helpers and edge-length preparation
- `add_edge_speeds`, `add_edge_travel_times`
- `shortest_path`, `k_shortest_paths`, `route_to_gdf`
- street statistics, bearings, and orientation entropy

Read `sub-skills/routing-analysis/SKILL.md` for weighting, optional nearest-neighbor dependencies, and route-analysis troubleshooting.

### `elevation-visualization`
Use this when the task is about node elevations, edge grades, or static plots.

Covers:
- raster or web elevation attachment
- edge grade calculation
- graph, route, figure-ground, footprint, and orientation plots
- headless plotting and image-output settings

Read `sub-skills/elevation-visualization/SKILL.md` for raster, matplotlib, and headless-output guidance.

## Common routing clues

- If the user mentions a city, address, boundary, building footprints, or transit stops, start with `data-acquisition`.
- If the user mentions a saved graph, GeoPackage, GraphML, OSM XML, CRS, projection, simplification, or validation, use `graph-modeling-io`.
- If the user mentions shortest paths, travel time, nearest nodes/edges, network statistics, or bearings, use `routing-analysis`.
- If the user mentions elevation, grades, or a saved image/plot, use `elevation-visualization`.
- If a task mixes workflows, complete prerequisites first and then route to the downstream sub-skill.

## Runtime notes

- Public package facts and the refresh baseline live in `references/repo-provenance.md`.
- The managed router metadata lives in `references/repo-routing-metadata.json`.
- The reusable smoke helpers live under `scripts/` or the owning sub-skill `scripts/` directories.
- Do not link runtime instructions to the original repository checkout; use the bundled references and scripts in this skill tree.
