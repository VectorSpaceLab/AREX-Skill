# OSMnx package overview

## Public package facts

- Distribution name: `osmnx`
- Import name: `osmnx`
- Installed snapshot used for this skill: 2.1.1
- Python support in package metadata: `>=3.11`
- Public top-level package exposes both module namespaces and the older v1 shortcut API through `osmnx.__init__`.
- The package does not publish a general command-line interface. Use Python imports and the bundled scripts in this skill tree.

## Optional extras that matter for this skill

| Extra | Adds support for | Where it matters |
| --- | --- | --- |
| `neighbors` | `scipy`, `scikit-learn` | nearest-node/edge searches on projected and unprojected graphs |
| `entropy` | `scipy` | orientation entropy |
| `raster` | `rasterio`, `rio-vrt` | local raster elevation and VRT-backed multi-raster sampling |
| `visualization` | `matplotlib` | graph, route, footprint, and orientation plots |

## Module map

| Module or shortcut | Main purpose | Owns workflow |
| --- | --- | --- |
| `osmnx.geocoder`, `osmnx.geocode`, `osmnx.geocode_to_gdf` | Resolve place names or OSM IDs to coordinates or GeoDataFrames | `data-acquisition` |
| `osmnx.graph`, `osmnx.graph_from_*` | Download or build street graphs from Overpass or local XML | `data-acquisition` |
| `osmnx.features`, `osmnx.features_from_*` | Download arbitrary OSM features as GeoDataFrames | `data-acquisition` |
| `osmnx.settings` | Cache, rate limit, HTTP headers, endpoint URLs, historical snapshots, and query defaults | `data-acquisition` |
| `osmnx.convert`, `osmnx._validate` | Graph/GeoDataFrame validation and conversion | `graph-modeling-io` |
| `osmnx.projection`, `osmnx.simplification`, `osmnx.truncate` | Projection, topology cleanup, and subgraph selection | `graph-modeling-io` |
| `osmnx.io` | GraphML, GeoPackage, and OSM XML persistence | `graph-modeling-io` |
| `osmnx.distance`, `osmnx.shortest_path`, `osmnx.k_shortest_paths` | Nearest-node/edge search and routing helpers | `routing-analysis` |
| `osmnx.routing`, `osmnx.stats`, `osmnx.bearing`, `osmnx.add_edge_bearings`, `osmnx.orientation_entropy` | Travel time, stats, and orientation analysis | `routing-analysis` |
| `osmnx.elevation`, `osmnx.add_edge_grades` | Raster or web elevation attachment and grades | `elevation-visualization` |
| `osmnx.plot` and its helpers | Static plotting, route overlays, figure-ground, footprints, and orientation roses | `elevation-visualization` |
| `osmnx.utils`, `osmnx.utils_geo` | Logging, citation strings, timestamps, and geometry helpers | shared support |

## Usage rules that tend to surprise people

- Bounding boxes are `(left, bottom, right, top)`.
- Point queries are `(lat, lon)`.
- `graph_from_place` and `features_from_place` need the geocoder result to be a Polygon or MultiPolygon.
- `features_from_*` tag dictionaries use union semantics across tag branches.
- `custom_filter` strings intersect conditions; lists represent alternatives.
- `nearest_nodes` uses `scipy` on projected graphs and `scikit-learn` on unprojected graphs.
- `plot_orientation` expects `bearing` attributes to already exist on the graph.
- `plot_figure_ground` expects an unprojected graph.
- `save_graph_xml` is for unsimplified, unprojected OSM-style export; graph persistence should usually use GraphML or GeoPackage instead.

## When to read the sub-skill references

- Read the data-acquisition workflow reference when choosing a query family or settings profile.
- Read the graph-modeling-io reference when validating a graph, repairing indexes, projecting CRS, or deciding a persistence format.
- Read the routing-analysis reference when reasoning about weights, nearest search, route lists, or statistics.
- Read the elevation and plotting references when working with rasters, grades, headless image generation, or route/footprint/orientation plots.
