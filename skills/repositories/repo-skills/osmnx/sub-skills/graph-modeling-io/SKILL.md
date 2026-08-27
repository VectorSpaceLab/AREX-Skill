---
name: graph-modeling-io
description: "Manipulate OSMnx NetworkX/GeoPandas graph data structures and
  persist or restore them safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Graph Modeling and I/O

Use this sub-skill when the task is about an existing OSMnx graph or GeoDataFrame: validating its schema, converting between NetworkX and GeoPandas representations, projecting CRS, simplifying or consolidating topology, truncating components, or saving/loading graph files.

## Route here

- Validate OSMnx graph, node/edge GeoDataFrame, or features GeoDataFrame invariants.
- Convert `MultiDiGraph`/`MultiGraph` objects to/from node and edge GeoDataFrames.
- Create directed/undirected graph views with `to_digraph` or `to_undirected`.
- Project geometries, GeoDataFrames, or graphs with `project_geometry`, `project_gdf`, or `project_graph`.
- Simplify topology, consolidate intersections, truncate by distance/bbox/polygon, or keep the largest weak/strong component.
- Persist or restore graph data with GraphML, GeoPackage, or OSM XML.

## Route elsewhere

- Downloading, geocoding, Overpass/Nominatim settings, OSM tag queries, or local XML acquisition belong to `data-acquisition`.
- Nearest-node/edge search, route computation, network statistics, bearings, orientation entropy, speeds, or travel times belong to `routing-analysis`.
- Elevation, grade calculation, and plotting belong to `elevation-visualization`.

## Operating references

Read these before acting:

1. [Data model and transformations](references/data-model.md) for graph/GDF invariants, validation, conversion, projection, simplification, consolidation, truncation, and difficult recovery patterns.
2. [Persistence and file formats](references/io-reference.md) for GraphML, GeoPackage, OSM XML, dtype restoration, and format-choice rules.
3. [Troubleshooting graph modeling and I/O](references/troubleshooting.md) for predictable validation, CRS, simplification, truncation, and save/load failures.

Bundled smoke script:

- [Graph/GDF/GraphML smoke test](scripts/validate_graph_io_smoke.py) creates a tiny graph, validates it, round-trips through GeoDataFrames, saves/loads GraphML in a temporary directory, and prints a concise success summary.

## Minimal workflow

1. Identify the object type: OSMnx `networkx.MultiDiGraph`, node/edge GeoDataFrames, features GeoDataFrame, geometry, or file path.
2. Validate early with `osmnx.convert.validate_graph`, `validate_node_edge_gdfs`, or `validate_features_gdf`.
3. Normalize the data model before analysis or persistence: ensure CRS, node `x`/`y`, edge `(u, v, key)` index, edge `osmid`, and edge `length` are present with compatible types.
4. Use projection before distance/tolerance operations that require metric units, then project back to lat-long only when needed for geographic output.
5. Choose persistence format deliberately: GraphML for future OSMnx work, GeoPackage for GIS layer exchange, OSM XML only for unsimplified/unprojected OSM-style export.
6. Run the bundled smoke script when an environment or installation may be suspect.
