# Troubleshooting Graph Modeling and I/O

Use this guide when validation, conversion, projection, topology cleanup, truncation, or persistence fails on an existing OSMnx graph/GDF.

## Validation failures

### `G.graph must have a 'crs' data attribute`

Cause: the graph lacks `G.graph["crs"]`, or it is `None`.

Fix:

```python
G.graph["crs"] = "epsg:4326"  # only if x/y are longitude/latitude
ox.convert.validate_graph(G, strict=False)
```

Do not guess CRS for external data. Check the source file metadata or upstream GeoDataFrame CRS first.

### `Nodes must have 'x' and 'y' data attributes`

Cause: nodes lack coordinate attributes.

Fix from a node GeoDataFrame:

```python
for node_id, row in gdf_nodes.iterrows():
    G.nodes[node_id]["x"] = float(row.geometry.x)
    G.nodes[node_id]["y"] = float(row.geometry.y)
```

If the graph is already built but only has geometries elsewhere, rebuild from clean node/edge GeoDataFrames.

### `Nodes should have 'street_count' data attributes`

Cause: strict validation expects `street_count` on every node. Some local XML imports or external graph builds omit it.

Fix options:

- For temporary conversion or file loading checks, use `validate_graph(G, strict=False)`.
- For a durable OSMnx graph, compute or assign a valid `street_count` before strict validation. If routing/statistics will use street counts, compute them with the routing-analysis/statistics workflow rather than filling arbitrary constants.

### `Edges must have 'osmid' data attributes` or `Edges must have 'length' data attributes`

Cause: external edge data is missing OSM ID or length.

Fix:

```python
for u, v, k, data in G.edges(keys=True, data=True):
    data.setdefault("osmid", k)  # use a real way/edge ID if available
    data.setdefault("length", data["geometry"].length if "geometry" in data else 0.0)
```

Use projected geometry length only when the graph CRS units are linear. For longitude/latitude coordinates, calculate geodesic lengths in the routing-analysis workflow or use known length values from the data source.

### Strict mode rejects a graph that seems usable

Cause: warning-level schema issues are elevated to errors: non-int node IDs, missing `street_count`, nonstandard `osmid`/`length` types, or nonnumeric coordinates.

Fix:

1. Run `ox.convert.validate_graph(G, strict=False)` to distinguish hard errors from warnings.
2. Repair types if the graph will be used by OSMnx algorithms.
3. Keep `strict=False` only as a documented temporary acceptance for data loaded from GIS/GraphML with known dtype drift.

## Node/edge GeoDataFrame conversion failures

### `gdf_nodes` and `gdf_edges` must be GeoDataFrames

Cause: one or both objects are pandas DataFrames.

Fix:

```python
import geopandas as gpd

gdf_nodes = gpd.GeoDataFrame(gdf_nodes, geometry="geometry", crs="epsg:4326")
gdf_edges = gpd.GeoDataFrame(gdf_edges, geometry="geometry", crs=gdf_nodes.crs)
```

Only set a CRS you know is correct.

### `gdf_nodes` must have 'x' and 'y' columns

Cause: node coordinates exist only as geometry.

Fix:

```python
gdf_nodes["x"] = gdf_nodes.geometry.x
gdf_nodes["y"] = gdf_nodes.geometry.y
```

### Node geometry differs from `x`/`y`

Cause: `graph_from_gdfs` ignores node geometry and uses `x`/`y`; strict validation fails when they disagree.

Fix by making geometry match coordinates:

```python
from geopandas import points_from_xy

gdf_nodes = gdf_nodes.copy()
gdf_nodes = gdf_nodes.set_geometry(points_from_xy(gdf_nodes["x"], gdf_nodes["y"]), crs=gdf_nodes.crs)
```

Or, if geometry is authoritative, overwrite `x`/`y` from geometry.

### Edge GeoDataFrame index is wrong

Cause: `gdf_edges` is not uniquely multi-indexed by `(u, v, key)`.

Fix:

```python
gdf_edges = gdf_edges.reset_index(drop=False)
if "key" not in gdf_edges:
    gdf_edges["key"] = 0
gdf_edges = gdf_edges.set_index(["u", "v", "key"])
gdf_edges.index.names = ["u", "v", "key"]
```

Then check uniqueness:

```python
if not gdf_edges.index.is_unique:
    raise ValueError("Duplicate edge (u, v, key) rows must be resolved before graph_from_gdfs.")
```

### Edges refer to missing nodes

Cause: some edge `u` or `v` IDs are absent from `gdf_nodes.index`.

Fix by either adding missing nodes from a trusted source or dropping dangling edges:

```python
node_ids = set(gdf_nodes.index)
mask = gdf_edges.index.get_level_values("u").isin(node_ids) & gdf_edges.index.get_level_values("v").isin(node_ids)
gdf_edges = gdf_edges.loc[mask]
```

## Projection and CRS issues

### `gdf must have a valid CRS and cannot be empty`

Cause: `project_gdf` received an empty GeoDataFrame or one with `crs=None`.

Fix: filter after projection when possible, or assign the correct CRS before projecting:

```python
if gdf.empty:
    raise ValueError("Cannot project an empty GeoDataFrame.")
if gdf.crs is None:
    gdf = gdf.set_crs("epsg:4326")  # only if coordinates are lon/lat
```

### Distance/tolerance results are nonsensical

Cause: you used longitude/latitude degrees where meters were expected.

Fix:

```python
if not ox.projection.is_projected(G.graph["crs"]):
    G = ox.projection.project_graph(G)
```

Use projected graphs for `consolidate_intersections(tolerance=...)`, geometry lengths, buffers, and metric spatial reasoning.

### Projecting back for OSM XML

OSM XML expects lon/lat-like coordinates. If you have a projected graph intended for XML export:

```python
G_latlong = ox.projection.project_graph(G_projected, to_latlong=True)
```

Still do not export if the graph is simplified.

## Simplification and consolidation failures

### `This graph has already been simplified`

Cause: `G.graph["simplified"]` is true.

Fix: do not simplify twice. Keep the original unsimplified graph if you may need to rerun with different `node_attrs_include`, `edge_attrs_differ`, or `edge_attr_aggs`.

### Simplification removed nodes you wanted to keep

Cause: those nodes were treated as interstitial geometry vertices.

Fix with endpoint relaxers:

```python
G_s = ox.simplification.simplify_graph(
    G,
    node_attrs_include=["highway"],
    edge_attrs_differ=["osmid", "lanes", "bike_lane"],
)
```

Use only attributes that are meaningful for your task; overusing relaxers can leave the graph barely simplified.

### Simplified edge attributes became lists or disappeared

Cause: OSMnx aggregates merged edge attributes. Missing/NaN values are omitted; multiple distinct values become lists unless an aggregation is specified.

Fix:

```python
G_s = ox.simplification.simplify_graph(
    G,
    edge_attr_aggs={"length": sum, "travel_time": sum, "lanes": "max"},
)
```

### `tolerance` values must be greater than zero

Cause: `consolidate_intersections` received zero or negative scalar/dict values.

Fix: use positive projected-distance values. For a desired maximum center-to-center merge distance of about 10 meters, start with `tolerance=5` because node buffers overlap.

### Consolidation merges ramps/bridges/dead-ends incorrectly

Causes:

- Graph is unprojected and tolerance is in degrees.
- `dead_ends=True` retained dead-ends you intended to discard.
- Long loop/ramp edges made nearby nodes topologically connected.

Fix:

```python
G_proj = ox.projection.project_graph(G)
G_c = ox.simplification.consolidate_intersections(
    G_proj,
    tolerance=8,
    dead_ends=False,
    max_length=80,
    rebuild_graph=True,
)
```

Tune tolerance and `max_length` to the local street design.

### Consolidated graph node IDs are not OSM IDs

Expected behavior: rebuilt consolidated graphs use cluster node IDs. Use node attribute `osmid_original` to inspect original OSM IDs.

## Truncation failures

### `Found no graph nodes within the requested polygon`

Cause: the polygon and graph coordinates do not overlap, often due to CRS mismatch or bbox order mistakes.

Fix:

- Ensure polygon CRS matches graph CRS before truncation.
- For bounding boxes, use `(left, bottom, right, top)`, not `(north, south, east, west)`.
- Check a small node GeoDataFrame plot or bounds comparison before truncating.

### Boundary edges disappear

Cause: node-based truncation removed outside endpoint nodes.

Fix: use `truncate_by_edge=True` for bbox/polygon truncation to retain outside nodes when at least one neighbor is inside.

### Distance truncation removes too much

Causes:

- `source_node` is in a small disconnected component.
- `weight` is missing or has unexpected units.
- Directed graph connectivity prevents reaching nodes.

Fix:

```python
G_main = ox.truncate.largest_component(G, strongly=False)
G_cut = ox.truncate.truncate_graph_dist(G_main, source_node, dist=1000, weight="length")
```

Validate the chosen `weight` exists and is numeric.

## GraphML issues

### `You must pass one and only one of filepath or graphml_str`

Cause: `load_graphml` received both or neither.

Fix:

```python
G = ox.io.load_graphml("graph.graphml")
# or
G = ox.io.load_graphml(graphml_str=graphml_text)
```

### Boolean values load incorrectly

Cause: custom boolean attributes were loaded with `bool`, where `bool("False")` is `True`.

Fix:

```python
G = ox.io.load_graphml(
    "graph.graphml",
    node_dtypes={"custom_bool": ox.io._convert_bool_string},
    edge_dtypes={"custom_bool": ox.io._convert_bool_string},
    graph_dtypes={"custom_bool": ox.io._convert_bool_string},
)
```

### `Invalid literal for boolean`

Cause: a supposedly boolean GraphML value is not exactly `"True"` or `"False"`.

Fix: inspect the attribute values and supply a custom converter if you have a third state such as `"yes"`, `"no"`, `"0"`, `"1"`, or empty string.

### Loaded GraphML fails strict validation due to custom dtypes

Cause: you overrode standard dtype conversion or the file was not saved by OSMnx.

Fix: load with dtype maps that restore required attributes, then validate:

```python
G = ox.io.load_graphml("graph.graphml", edge_dtypes={"length": float})
ox.convert.validate_graph(G, strict=False)
```

Use strict validation once required dtypes are repaired.

## GeoPackage issues

### File-driver/import error while saving or reading `.gpkg`

Cause: GeoPandas file I/O dependencies or GDAL drivers are unavailable in the environment.

Fix:

- Prefer GraphML if you do not specifically need GIS exchange.
- Install/repair the GeoPandas file I/O stack appropriate to your environment.
- Test with a tiny GeoDataFrame write/read before exporting a large graph.

### Reconstructed graph has string `osmid` or mixed attribute types

Cause: GeoPackage stores mixed non-numeric columns as strings.

Fix:

```python
gdf_edges["osmid"] = gdf_edges["osmid"].astype(int)  # only if all values are scalar ints
G = ox.convert.graph_from_gdfs(gdf_nodes, gdf_edges)
ox.convert.validate_graph(G, strict=False)
```

For exact arbitrary Python attributes, use GraphML instead of GeoPackage.

## OSM XML issues

### `Graph must be unsimplified to save as OSM XML`

Cause: `save_graph_xml` was called on a simplified graph.

Fix: keep or reacquire an unsimplified graph with `simplify=False`. You cannot reliably reverse simplification to recover the original OSM way segmentation.

### Warning about `ox.settings.all_oneway=True`

Cause: OSMnx cannot know that the graph was created with all-oneway semantics.

Fix: for graphs intended for XML export, set `ox.settings.all_oneway = True` before acquiring the unsimplified graph, then restore the previous setting after export.

### Warning about projected graph being saved as XML

Cause: projected `x`/`y` coordinates would be written as XML lon/lat.

Fix:

```python
if ox.projection.is_projected(G.graph["crs"]):
    G = ox.projection.project_graph(G, to_latlong=True)
```

### Loading OSMnx-generated XML warns or behaves unexpectedly

Expected behavior: OSM XML export is for external XML use, not OSMnx persistence. Use GraphML for save/load workflows.

## Environment smoke check

If graph modeling or I/O behavior looks like an installation problem rather than a data problem, run:

```bash
python path/to/scripts/validate_graph_io_smoke.py
python path/to/scripts/validate_graph_io_smoke.py --help
```

The smoke script requires only installed OSMnx and its normal base dependencies. It creates a tiny graph, validates graph/GDF round-trip behavior, saves/loads GraphML in a temporary directory, and prints a success summary.
