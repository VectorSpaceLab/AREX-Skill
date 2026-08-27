# Routing reference

This sub-skill covers coordinate-to-graph matching, edge-length and edge-weight preparation, shortest-path solving, k-shortest-path generation, and route GeoDataFrame extraction.

## Coordinate and CRS conventions

- `nearest_nodes` and `nearest_edges` expect `X` then `Y`:
  - `X` = x / longitude / easting
  - `Y` = y / latitude / northing
- `great_circle` expects `lat1, lon1, lat2, lon2`.
- `euclidean` expects `y1, x1, y2, x2`.
- `add_edge_lengths` should be run on an **unprojected, unsimplified** graph.
- `nearest_nodes` chooses the backend from the graph CRS:
  - projected graph → `scipy` / cKDTree
  - unprojected graph → `scikit-learn` / BallTree
- `nearest_edges` is geometry-based and works best on projected coordinates.

## Verified APIs

| Function | Signature | What it returns |
| --- | --- | --- |
| `distance.great_circle` | `(lat1, lon1, lat2, lon2, earth_radius=6371009)` | Scalar or vectorized great-circle distance in meters by default. |
| `distance.euclidean` | `(y1, x1, y2, x2)` | Scalar or vectorized Euclidean distance in the input units. |
| `distance.add_edge_lengths` | `(G, *, edges=None)` | The same graph with a `length` edge attribute in meters. |
| `distance.nearest_nodes` | `(G, X, Y, *, return_dist=False)` | Node ID(s), or `(node_id(s), distance(s))` if requested. |
| `distance.nearest_edges` | `(G, X, Y, *, return_dist=False)` | `(u, v, key)` edge tuple(s), or `(edge_tuple(s), distance(s))`. |
| `routing.add_edge_speeds` | `(G, *, hwy_speeds=None, fallback=None, agg=np.mean)` | The same graph with `speed_kph` edge attributes. |
| `routing.add_edge_travel_times` | `(G)` | The same graph with `travel_time` edge attributes in seconds. |
| `routing.shortest_path` | `(G, orig, dest, *, weight='length', cpus=1)` | A node path, or one path per OD pair, or `None` for an unsolved pair. |
| `routing.k_shortest_paths` | `(G, orig, dest, k, *, weight='length')` | Iterator over the next-shortest node paths. |
| `routing.route_to_gdf` | `(G, route, *, weight='length')` | Ordered route edges as a GeoDataFrame. |

## Length and distance helpers

### `distance.great_circle`

- Use for geographic coordinates in decimal degrees.
- Returns meters when you keep the default Earth radius.
- Vectorized arrays are accepted.

### `distance.euclidean`

- Use for projected coordinates or any other linear unit.
- The function does **not** project data for you.
- This is the right helper when the graph and query points are already in the same planar CRS.

### `distance.add_edge_lengths`

- Computes straight-line lengths between each edge's incident nodes.
- Good for fresh, unsimplified graphs.
- If you call it on already-simplified or projected data, the values are only straight-line approximations in the graph's current coordinate space.
- The optional `edges` argument can update a subset of `(u, v, key)` edges.

## Nearest matching

### `distance.nearest_nodes`

- Accepts a scalar coordinate pair or iterables of coordinates.
- Returns a scalar node ID for one point or an array of node IDs for many points.
- With `return_dist=True`, also returns the nearest distance(s).
- Distances are in meters for unprojected graphs and in graph units for projected graphs.
- Batch search is preferred over looping.

### `distance.nearest_edges`

- Accepts the same scalar/vectorized input pattern as `nearest_nodes`.
- Returns edge tuples `(u, v, key)` rather than node IDs.
- If several edges share the same geometry, any one of the equally good matches may be returned.
- Use projected coordinates if you want meaningful distance values.

## Edge speeds, lengths, and travel times

### `routing.add_edge_speeds`

- Writes `speed_kph` values to all edges.
- Cleans common `maxspeed` formats, including numeric strings, `mph`, and pipe-separated values.
- If you have highway-type speed defaults, pass them through `hwy_speeds`.
- If a highway type has no usable speed data, `fallback` can fill the gap.
- If the graph has no usable speed information at all and you do not supply defaults, the function raises a `ValueError`.

### `routing.add_edge_travel_times`

- Requires both `length` and `speed_kph` on every edge.
- Writes `travel_time` in seconds.
- Run `add_edge_lengths` and `add_edge_speeds` first.

## Route solving and route GeoDataFrames

### `routing.shortest_path`

- Uses Dijkstra's algorithm.
- With scalar `orig` and `dest`, returns one node path.
- With iterable `orig` and `dest`, both sides must be iterable and have equal length.
- `cpus=None` uses all available CPUs.
- `cpus=1` is the safest debugging choice.
- When a route cannot be solved, the function returns `None` for that origin/destination pair.
- The `weight` argument must name a numeric edge attribute.

### `routing.k_shortest_paths`

- Uses Yen's algorithm.
- Returns an iterator, not a list.
- Materialize it with `list(...)` if you need to inspect all candidate routes.
- The shortest-path graph is collapsed to a digraph by choosing the minimum edge weight among parallel edges.

### `routing.route_to_gdf`

- Takes a **node path** such as the output of `shortest_path`.
- Returns the edges in route order as a GeoDataFrame.
- The route is indexed by `(u, v, key)`.
- Use the same `weight` you used for routing when you want the route GeoDataFrame to choose the same parallel edge.

## Batch OD routing notes

- Batch routing works best when `orig` and `dest` are arrays or lists of equal length.
- `cpus=None` is useful for large batches; `cpus=1` is easier to debug.
- Protect your own script entry point with `if __name__ == "__main__":` before using multiprocessing.
- If some OD pairs are unreachable, the returned list can contain `None` values.

## Validation checklist

1. Ensure the graph already exists and has `x`, `y`, and `crs`.
2. Add `length` before any time-based routing.
3. Add `speed_kph` before `travel_time`.
4. Keep query coordinates in the same CRS as the graph.
5. Use `route_to_gdf` only after you have a node path.
6. Use `weight` names that really exist and contain numeric values.
