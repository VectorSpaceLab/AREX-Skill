# Distance, CRS, and geometry contract

Spatial topology is only meaningful when coordinates, units, graph costs, and
geometry semantics agree. Treat CRS selection as an input decision, not a
post-processing detail.

## CRS checklist

1. Confirm every layer has a CRS before combining layers or requesting network
   distances. `group_nodes` explicitly rejects missing CRS on either input;
   directed proximity checks source and target CRS equality; network metrics
   check the input CRS against `network_gdf` when the input CRS is set.
2. Prefer a projected CRS appropriate to the study area for distances, lengths,
   buffers, centroids, tessellation, and areas. A geographic CRS such as
   longitude/latitude expresses coordinates in angular units. The package does
   not generally convert those units to metres for proximity or geometry
   calculations.
3. Reproject all interacting layers with `to_crs`, not `set_crs`, when the
   coordinates are already in another CRS. Use `harmonize_crs` when an area
   GeoDataFrame/GeoSeries should be aligned to an edge layer; it reprojects and
   warns by default. A raw Shapely `Polygon` has no CRS and is assumed to be in
   the edge coordinate system.
4. For a network metric, reproject the sample layer and network together before
   building the graph. Do not use a network in degrees with samples in metres,
   even if the numeric coordinates look similar.
5. Read warnings as contract failures: `dual_graph` warns before taking
   centroids in a geographic CRS, but most proximity and geometry helpers do
   not issue an equivalent warning. A lack of warning does not make angular
   distances valid.

Example preparation:

```python
study_crs = "EPSG:27700"  # choose a CRS suitable for the study area
points = points.to_crs(study_crs)
polygons = polygons.to_crs(study_crs)
network = network.to_crs(study_crs)
```

## The three distance metrics

### Euclidean

Euclidean distance is the L2 distance between centroid-derived `(x, y)`
positions. Edge weights are coordinate units. Euclidean edge geometry is a
straight `LineString` between the two positions. Point inputs use their point
coordinates; polygon inputs use centroids unless a point override is supplied.

The ordinary point builders use spatial indexes for neighbour selection. The
Delaunay, Gabriel, and relative-neighbourhood candidate predicates are based on
planar coordinates. In particular, selecting `distance_metric="manhattan"` or
`"network"` changes the weights and drawn paths for these candidate edges but
does not turn the Gabriel/RNG emptiness test into a Manhattan/network metric.

### Manhattan

Manhattan distance is the L1/city-block distance:

```text
abs(x2 - x1) + abs(y2 - y1)
```

The generated geometry is an axis-aligned L path through `(x2, y1)` (including
coincident vertices when the path is aligned). Use a projected, locally
rectilinear coordinate system when this is intended to approximate street
movement. It is not a road-network shortest path and does not avoid barriers.

### Network

Network distance is a shortest-path distance over `network_gdf`:

1. Convert the line network to NetworkX and read its node `pos` coordinates.
2. Build a nearest-node KD-tree over those positions.
3. Snap each sample position to one nearest network node.
4. Run Dijkstra using `network_weight`, or an automatically resolved weight.
5. Use the shortest path length for `weight`; use network node positions for the
   edge `LineString` where a path has at least two nodes.

The support network must be non-null, same-CRS as the samples, convertible to a
NetworkX graph with valid node positions, and connected for the pairs that need
finite distances. The default weight resolution is:

- numeric `network_weight` attribute when explicitly requested;
- otherwise the cached `__c2g_edge_length` if already present;
- otherwise `geometry.length` for each network edge;
- otherwise the Euclidean distance between edge endpoints' `pos` values;
- otherwise `0.0` when neither geometry nor both endpoint positions are usable.

An explicit weight name must be numeric on every network edge. Missing or
non-numeric values raise a `ValueError`. Zero or misleading fallback weights
are accepted by the implementation, so validate the network table yourself.
Negative weights are not a valid Dijkstra cost contract.

Network distances are node-snapped approximations. A point close to an edge can
snap to a farther endpoint, and two points snapping to the same node receive
zero network separation even when their direct geometric separation is nonzero.
The latter case uses a non-degenerate direct segment as output geometry. A
missing path also falls back to a direct sample segment for edge geometry, while
its weight remains `inf` when the pair was retained by a builder that allows it.
Disconnected pairs are `inf`; bounded radius and neighbour selection exclude
infinite destinations. A spanning tree over a disconnected support network
cannot represent meaningful finite connectivity; inspect weights and
components before accepting it.

Network selection is sparse for KNN, fixed-radius, and directed builders. Fixed
radius passes its cutoff to Dijkstra and includes exact-boundary paths. Waxman
is intentionally different: it materialises a dense matrix and dense random
array to keep seeded sampling stable.

## Position and geometry rules

- Input index values become node identifiers. Never reset or reorder the index
  without carrying the mapping to downstream edge tables.
- `GraphBuilder` stores node `pos` from centroids but preserves input attributes
  and geometry in node output. Edges get `weight` and a relationship geometry.
- `node_geom_col` is an ordinary column holding point geometries. It changes the
  positions used for edge measurement; it is not automatically made the active
  geometry unless `set_point_nodes=True`.
- `set_point_nodes=True` saves the original active geometry under
  `original_geometry` and replaces active node geometry with the selected
  points. This is useful for heterogeneous graph conversion but loses direct
  polygon plotting unless the original column is used separately.
- `duplicate_edges=True` appends reverse MultiIndex rows and reverses copied
  `LineString` geometries. It does not make a NetworkX `Graph` directed or
  duplicate graph edges in memory.
- `canonicalize_edges` only changes index order and duplicate handling; it does
  not reverse geometries. Do not assume a canonical `(u,v)` row starts at the
  canonical `u` endpoint unless the source geometry was normalised separately.

## Area and predicate semantics

`group_nodes` uses a spatial join with points on the left and polygons on the
right. Its default `covered_by` includes points on polygon boundaries. The
`within` predicate excludes boundary points. The output relation key is
canonicalised independently of the GeoPandas predicate wording (`covers` for
`covered_by`, `contains` for `within` and `contains`). Validate custom
predicates with a tiny geometry fixture; a predicate that is valid in the
opposite operand direction can legitimately return no rows.

`contiguity_graph` derives adjacency from polygon boundaries using libpysal:
Queen includes shared vertices, while Rook requires shared boundary edges. Its
weights and edge paths are measured between the chosen node positions, not
along the common polygon boundary.

## Post-processing geometry

### Reachability and isochrones

Graph reachability uses edge costs, not geometric length unless `edge_attr` is
`"length"` or the requested attribute is injected from edge geometry. Centers
snap to the nearest graph node by `pos`; a far-away center is still snapped.
Multiple centers are a union of sources. In `create_isochrone`, a threshold
sequence computes shortest-path distances once at the maximum threshold and
then materialises each layer in caller order.

The isochrone geometry method controls which reachable geometries are used:

- KNN concave hull: node positions only; retries larger neighbourhoods, then
  an alpha fallback if a closed valid polygon cannot be made.
- Alpha concave hull: node positions and edge geometries.
- Convex hull: node positions only.
- Buffer: node positions and edge geometries, buffered by map units.

Components are processed independently. A point or line result is buffered by a
small default distance when a polygonal output is required. A no-position graph,
empty center sequence, invalid geometry collection, or collapsed negative
buffer can produce a typed empty result. `cut_edge_types` is applied after
shortest-path reachability; use it to change the envelope topology, not to
exclude those edges from routing.

### Tessellation

Tessellation parameters are map-unit values. Morphological tessellation uses
building-like input directly with momepy. Enclosed tessellation uses
`primary_barriers` to form enclosures. When `limit` is omitted, city2graph
constructs a non-convex buffered union of buildings and barriers using a
100-unit buffer, then clips enclosures to it. This avoids giant outer cells but
means the 100-unit value is scale-dependent; supply an explicit projected limit
when the default is inappropriate.

The enclosed retry ladder is deterministic and should be treated as part of the
output contract:

1. Try momepy with caller options.
2. For known geometry-type/GEOS failures, try `grid_size=1e-3` unless the
   caller pinned `grid_size`.
3. Retry with deterministic vertex jitter if precision alone is insufficient.
4. If known failures persist, return a typed empty result for that failed unit;
   unrelated exceptions propagate.
5. Silently overlapping or under-covering cells are detected by area/union
   checks, retried, and then dropped by enclosure if still degenerate.
6. GeometryCollections are reduced to polygonal pieces; empty/non-polygonal
   cells are removed.

For rectilinear data, expect the precision/jitter rungs to matter. Keep
`n_jobs=1` while diagnosing reproducibility or a geometry failure. Explicit
`grid_size` is respected and is never overwritten.

### Clipping and dual graphs

`clip_graph` first aligns an area GeoDataFrame/GeoSeries to the edge CRS. With
the default strict mode, lines are clipped, MultiLineStrings are exploded,
nodes outside the area are removed, and edges whose MultiIndex endpoints are not
both in-bound are removed. With `keep_outer_neighbors=True`, intersecting edges
are retained as whole geometries and outside endpoint nodes can remain. A raw
Shapely area is used as-is; reproject it yourself.

`dual_graph` takes centroids of primal edge geometries. It warns for geographic
CRS but still computes unless the caller stops. Original primal edge attributes
are copied into dual nodes. Dual edges connect pairs of primal edges that share
an endpoint, and their geometry joins dual centroids. This is a topological
line-graph-like operation; it does not test geometric intersection of arbitrary
line shapes.
