# Persistence and File Format Reference

Use this reference to choose a graph persistence format and call OSMnx I/O functions safely. For later OSMnx analysis, GraphML is the default choice.

## Format decision table

| Need | Use | Why | Avoid |
|---|---|---|---|
| Save and reload the same graph for future OSMnx/NetworkX work | GraphML: `save_graphml` + `load_graphml` | Preserves graph/node/edge attributes as strings and restores standard OSMnx dtypes on load. Works without GIS file drivers. | Do not use OSM XML for OSMnx round-trips. |
| Exchange nodes/edges with GIS tools | GeoPackage: `save_graph_geopackage` | Writes separate `nodes` and `edges` layers readable by GIS software and GeoPandas. | Requires GeoPandas file I/O stack. Non-numeric columns are stringified. |
| Export an OSM-like XML file for another application that requires OSM XML | OSM XML: `save_graph_xml` | Writes OSM `<node>` and `<way>` elements. | Only for unsimplified, preferably unprojected graphs created with all-oneway semantics. Not for later OSMnx reloading. |

## GraphML

Verified signatures:

- `save_graphml(G, filepath=None, *, gephi=False, encoding="utf-8") -> None`
- `load_graphml(filepath=None, *, graphml_str=None, node_dtypes=None, edge_dtypes=None, graph_dtypes=None) -> nx.MultiDiGraph`

Typical save/load:

```python
from pathlib import Path
import osmnx as ox

fp = Path("graph.graphml")
ox.io.save_graphml(G, fp)
G2 = ox.io.load_graphml(fp)
ox.convert.validate_graph(G2, strict=False)
```

`save_graphml` behavior:

- Creates the parent folder when needed.
- Copies the graph before stringifying values, so the caller's original graph is not mutated.
- Stringifies graph, node, and edge attribute values because GraphML stores scalar text values.
- If `gephi=True`, rewrites edge keys so each edge has a unique key/id for Gephi compatibility. Use this only when exporting to Gephi, because edge keys may no longer match the original graph.

`load_graphml` behavior:

- Pass exactly one of `filepath` or `graphml_str`.
- Reads as a forced multigraph and uses the node `osmid` dtype to parse node IDs.
- Removes GraphML `node_default` and `edge_default` metadata from `G.graph`.
- Converts stringified standard graph flags (`simplified`, `consolidated`), node attributes, edge attributes, and edge WKT `geometry` back to Python/Shapely objects where defaults or user-provided dtype maps say how.
- Literal stringified lists/dicts/sets are parsed with `ast.literal_eval` before dtype conversion.

Default dtype restoration includes:

| Scope | Defaults restored |
|---|---|
| Graph | `simplified`, `consolidated` as booleans |
| Nodes | `osmid` int, `x`/`y` float, `street_count` int, elevation fields float |
| Edges | `osmid` int or list of ints, `length` float, `oneway` boolean, `reversed` boolean, `speed_kph` float, `travel_time` float, `bearing`/`grade` fields float, `geometry` WKT to Shapely |

Custom dtype examples:

```python
# Preserve a custom boolean graph/node/edge attribute.
G2 = ox.io.load_graphml(
    "graph.graphml",
    graph_dtypes={"my_flag": ox.io._convert_bool_string},
    node_dtypes={"my_flag": ox.io._convert_bool_string},
    edge_dtypes={"my_flag": ox.io._convert_bool_string},
)

# Accept non-standard string IDs or lengths for diagnosis only.
G2 = ox.io.load_graphml(
    "graph.graphml",
    node_dtypes={"osmid": str},
    edge_dtypes={"osmid": float, "length": str},
)
ox.convert.validate_graph(G2, strict=False)
```

Boolean warning: do not use Python `bool` to convert the strings `"True"` and `"False"`; `bool("False")` is `True`. Use `ox.io._convert_bool_string` for strict `"True"`/`"False"` parsing.

## GeoPackage

Verified signature:

- `save_graph_geopackage(G, filepath=None, *, directed=False, encoding="utf-8") -> None`

Typical save:

```python
import osmnx as ox

ox.io.save_graph_geopackage(G, "graph.gpkg", directed=True)
```

Behavior:

- Creates the parent folder when needed.
- Writes two layers: `nodes` and `edges`.
- If `directed=True`, writes the directed graph as-is.
- If `directed=False`, first calls `to_undirected(G)` and writes one edge for each undirected street representation while retaining original oneway/from/to information as attributes.
- Converts every non-numeric, non-geometry column to string for reliable file serialization of mixed Python values.

Reading a saved GeoPackage back into OSMnx is a GeoPandas workflow:

```python
import geopandas as gpd
import osmnx as ox

gdf_nodes = gpd.read_file("graph.gpkg", layer="nodes").set_index("osmid")
gdf_edges = gpd.read_file("graph.gpkg", layer="edges").set_index(["u", "v", "key"])
G2 = ox.convert.graph_from_gdfs(gdf_nodes, gdf_edges, graph_attrs={"crs": gdf_edges.crs})
ox.convert.validate_graph(G2, strict=False)  # file drivers may round-trip some attrs as strings
```

GeoPackage is not as faithful as GraphML for arbitrary Python attributes. It is best for GIS exchange, not exact OSMnx object persistence.

## OSM XML export

Verified signature:

- `save_graph_xml(G, filepath=None, *, way_tag_aggs=None, encoding="utf-8") -> None`

Use only when a downstream application requires OSM XML. For OSMnx save/load round-trips, use GraphML instead.

Hard rules:

- `G` must be unsimplified. If `G.graph["simplified"]` is true, OSMnx raises `GraphSimplificationError` because one simplified edge may represent multiple OSM ways and cannot be serialized correctly as way segments.
- Prefer an unprojected graph (`epsg:4326`/lat-long). OSMnx warns if the graph CRS is projected because the projected `x`/`y` values would be written as XML `lon`/`lat` attributes.
- The graph should have been created while `ox.settings.all_oneway=True`. OSMnx warns if that setting is not currently true, because edge directions and way grouping may not match XML expectations.
- It is an export format, not the recommended reload path. Loading OSM XML generated by OSMnx can warn and may not behave as expected.

Typical safe export sequence:

```python
import osmnx as ox

# Before acquiring an OSM graph intended for XML export:
old_all_oneway = ox.settings.all_oneway
try:
    ox.settings.all_oneway = True
    # acquire an unsimplified graph in the data-acquisition workflow:
    # G = ox.graph.graph_from_...(..., simplify=False)
    ox.convert.validate_graph(G, strict=False)
    if G.graph.get("simplified"):
        raise ValueError("Do not save simplified graphs as OSM XML; reacquire or keep an unsimplified graph.")
    if ox.projection.is_projected(G.graph["crs"]):
        G = ox.projection.project_graph(G, to_latlong=True)
    ox.io.save_graph_xml(G, "graph.osm", way_tag_aggs={"lanes": "sum"})
finally:
    ox.settings.all_oneway = old_all_oneway
```

`way_tag_aggs`:

- Keys are OSM way tag names.
- Values are aggregation functions accepted by pandas `.agg()`.
- If no aggregation is provided for a tag, OSMnx uses the first edge's value for that way.

Export behavior:

- Adds standard default OSM element attributes when missing (`changeset`, `timestamp`, `uid`, `user`, `version`, `visible`).
- Rounds lat/lon coordinates to 7 decimals.
- Writes XML root metadata, bounds, nodes, and ways.
- Groups edges by OSM way ID and topologically sorts way nodes. If a way contains cycles, OSMnx may break cycles to produce an order and logs a warning.

## Safe end-to-end persistence patterns

### Exact working copy for a later OSMnx session

```python
ox.convert.validate_graph(G, strict=False)
ox.io.save_graphml(G, "work.graphml")
G_work = ox.io.load_graphml("work.graphml")
ox.convert.validate_graph(G_work, strict=False)
```

### GIS handoff with explicit layer reload

```python
ox.io.save_graph_geopackage(G, "network.gpkg", directed=True)
# Later, if needed for OSMnx again:
gdf_nodes = gpd.read_file("network.gpkg", layer="nodes").set_index("osmid")
gdf_edges = gpd.read_file("network.gpkg", layer="edges").set_index(["u", "v", "key"])
G_gis = ox.convert.graph_from_gdfs(gdf_nodes, gdf_edges)
```

### XML export without corrupting an analysis graph

```python
G_xml = G.copy()
if G_xml.graph.get("simplified"):
    raise ValueError("Keep or reacquire an unsimplified graph for OSM XML export.")
if ox.projection.is_projected(G_xml.graph["crs"]):
    G_xml = ox.projection.project_graph(G_xml, to_latlong=True)
ox.io.save_graph_xml(G_xml, "network.osm")
```

## What not to do

- Do not save a simplified graph as OSM XML.
- Do not rely on OSM XML for exact OSMnx graph persistence.
- Do not use GeoPackage when you need exact Python attribute types without custom repair after reading.
- Do not omit `graph_attrs` in `graph_from_gdfs` if you must preserve graph-level flags or metadata beyond CRS.
- Do not forget that GeoPackage/GIS reloads often require `strict=False` validation while you inspect and restore standard dtypes.
