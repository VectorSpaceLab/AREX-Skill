---
name: "routing-analysis"
description: "Routes OSMnx nearest-node and nearest-edge matching, edge
  weighting, routing, route GeoDataFrames, street statistics, bearings, and
  orientation entropy."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# routing-analysis

Use this sub-skill when you need to match coordinates to an existing OSMnx graph, add or inspect edge weights, solve routes, convert routes to GeoDataFrames, or compute network statistics, bearings, and orientation entropy.

## Use this route for

- `nearest_nodes` and `nearest_edges` on projected or unprojected graphs.
- `great_circle`, `euclidean`, and `add_edge_lengths` for distance and length preparation.
- `add_edge_speeds` and `add_edge_travel_times` for `speed_kph` and `travel_time` edge attributes.
- `shortest_path`, batch origin/destination routing with `cpus`, and `k_shortest_paths`.
- `route_to_gdf` for ordered edge-level route output.
- `count_streets_per_node`, `basic_stats`, and the lower-level street-stat helpers.
- `add_edge_bearings` and `orientation_entropy` on unprojected graphs.

## Do not use this route for

- Graph acquisition, geocoding, or OSM feature downloads. Use `../data-acquisition/SKILL.md`.
- Projection, graph/GeoDataFrame conversion, or persistence. Use `../graph-modeling-io/SKILL.md`.
- Plotting routes or orientation diagrams. Use `../elevation-visualization/SKILL.md`.

## Read first

- `references/routing-reference.md` for routing, nearest-match, weight, and route-to-GeoDataFrame details.
- `references/analysis-reference.md` for stats, bearings, and orientation analysis details.
- `references/troubleshooting.md` for the predictable routing, weight, and optional-dependency failures.
- `scripts/routing_analysis_smoke.py --help` for the deterministic local smoke check.

## Skill-owned script

- `scripts/routing_analysis_smoke.py` — builds a tiny deterministic graph and exercises lengths, speeds, travel times, routing, route conversion, stats, bearings, orientation entropy, and nearest matching when the optional dependencies are available.

## Typical workflow

1. Confirm the graph already exists and has the right CRS for the task.
2. Add or verify edge lengths, then add speeds and travel times before routing by time.
3. Use `nearest_nodes` or `nearest_edges` to map coordinates onto the graph.
4. Solve one route, many routes, or `k_shortest_paths` as needed.
5. Convert the node path to a route GeoDataFrame when you need ordered edge output.
6. Compute stats or orientation metrics on an undirected view when appropriate.
7. Run the smoke script when you need a fast local check.

## Cross-links

- If the graph still needs to be downloaded or geocoded, switch to `../data-acquisition/SKILL.md`.
- If you need to project, simplify, validate, convert, or save the graph, switch to `../graph-modeling-io/SKILL.md`.
- If the request is actually about plotting routes or orientation roses, switch to `../elevation-visualization/SKILL.md`.
