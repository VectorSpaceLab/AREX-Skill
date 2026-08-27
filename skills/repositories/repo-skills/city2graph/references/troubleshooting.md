# city2graph troubleshooting

## Installation and imports

- Install the core package for GeoPandas, Shapely, NetworkX, rustworkx,
  DuckDB, SciPy, and spatial workflows. Add the package `cpu` extra for
  PyTorch Geometric conversion. Probe `city2graph.is_torch_available()` and
  import both `torch` and `torch_geometric` before using PyG functions.
- An import failure is usually an environment/dependency problem, not a graph
  schema problem. Check the package version and `pip check`, then import the
  smallest relevant module. Do not repair a working environment by installing
  every optional extra.
- CUDA visibility is not proof that a CUDA operation can run. A shared or
  memory-constrained GPU can make a device allocation fail even when
  `torch.cuda.is_available()` is true. Use explicit `device="cpu"` for the
  verified baseline and report GPU status separately.

## CRS, units, and geometry

- Reproject layers to one suitable projected CRS before lengths, distances,
  buffers, tessellation, network budgets, centroids used as metric positions,
  or morphology. EPSG:4326 coordinates are degrees; city2graph warns but does
  not infer a local metric CRS.
- Ensure every non-empty node, edge, network, building, segment, zone, stop,
  and connector layer that participates in one operation has a compatible CRS.
  Reproject auxiliary geometry columns too when they carry a CRS.
- Validate expected geometry types before calling a builder. Null or empty
  geometries may produce typed empty output or dropped edges; distinguish that
  from a failed import. For graph round trips, decide whether original WKB
  geometry metadata is required or whether centroid/straight-line geometry is
  acceptable.

## IDs, indexes, and output schemas

- Node IDs are GeoDataFrame index values unless an API explicitly promotes an
  ID column. Non-empty edge endpoints are the first two levels of a
  MultiIndex; a third level is an edge key. Confirm endpoints exist in the
  intended node namespace, including each typed namespace in heterogeneous
  inputs.
- Homogeneous and heterogeneous forms are not interchangeable: use one frame
  for a homogeneous graph, or `dict[str, GeoDataFrame]` nodes and
  `dict[(src, relation, dst), GeoDataFrame]` edges for typed graphs.
- Empty outputs can have a deliberately reduced placeholder index while
  retaining canonical columns. Branch on `.empty` and validate required
  columns rather than requiring the populated-frame index shape.
- Preserve `graph_metadata` on PyG objects and `G.graph` on NetworkX objects.
  A manually assembled bare graph may lack CRS, original indexes, type maps,
  positions, or geometry needed for reconstruction.

## Directionality and duplicates

- Decide `directed`, reciprocal rows, `multigraph`, edge keys, self-loops, and
  canonicalization before conversion. Undirected PyG and OD routes may
  symmetrize or aggregate reciprocal edges; they reject ambiguous duplicate
  unordered pairs rather than preserving an unknown meaning.
- For heterogeneous undirected cross-type PyG relations, provide explicit
  reverse edge types when strict mode requires them. Generated reverse stores
  are message-passing artifacts and are not original input tables.
- Use `canonicalize_edges` to retain one undirected orientation or
  `symmetrize_edges` to materialize missing reverse rows. Neither operation
  guesses domain semantics or reverses an edge's meaning beyond geometry
  orientation.

## Spatial and morphology failures

- Network distances require a usable projected network graph, node positions,
  and a valid numeric edge-weight choice. city2graph snaps samples to nearest
  network nodes; it does not project samples onto edges. Unreachable paths are
  infinite and are excluded from bounded selection.
- Delaunay-family builders can fail on collinear or duplicate coordinates;
  preflight coordinates, jitter only when reproducibility allows it, or choose
  KNN/radius/MST alternatives. Tessellation retry/fallback warnings must be
  recorded; do not treat an empty fallback as a normal populated result.
- Morphology has separate walking-network and perpendicular-access caps.
  `clipping_buffer` supplies context and is not walking distance. Barrier-only
  rows are not movement nodes; a null alternative barrier geometry does not
  remove a movement row. Check place/movement edge endpoints and fallback
  warnings.

## Mobility, transit, and ingestion failures

- OD inputs need unique zone IDs, valid source/target overlap, numeric weights,
  and an explicit matrix type. Labeled adjacency matrices need equal index and
  column labels; NumPy arrays assume zone row order. Unknown endpoints,
  nonnumeric values, NaNs, and negative flows are warned or rejected according
  to the selected path.
- GTFS and GBFS loaders accept local files/directories. Inspect DuckDB tables
  after loading; a readable archive may still lack tables required by a chosen
  graph operation. GTFS summary/geometry workflows need the DuckDB `spatial`
  extension and usable stop coordinates or geometry. GBFS loading is ingestion,
  not an automatic transit graph builder.
- GTFS dates use `YYYYMMDD`; times use `HH:MM:SS` and may exceed 24 hours.
  Keep calendar bounds, exceptions, time windows, positive travel times, and
  frequency expansion explicit. An inverted or out-of-range window is a data
  selection error, not evidence of no transit service.
- Overture acquisition requires exactly one of `area` and `place_name`, a
  valid layer type, the `overturemaps` CLI, and network/service access. Use a
  polygon rather than a bare bbox when precise clipping matters. Treat output
  paths and prefixes as explicit, reviewable values because existing files may
  be overwritten. Use mocks/local fixtures for offline checks.
- Process Overture segments in a projected CRS before computing lengths,
  endpoint thresholds, or passable `barrier_geometry`. Connector metadata is
  normalized fractional position data; malformed records are ignored, but
  out-of-range fractions should be rejected upstream.

## Deprecations and external services

- Prefer GeoDataFrame output followed by `gdf_to_nx`; treat `as_nx=True`
  deprecation warnings as migration guidance.
- Do not silently retry live Nominatim, Overture, GTFS, or GBFS requests. Check
  user-agent/rate-limit policy, DNS, credentials, release availability, and
  network permissions explicitly, and keep a local boundary/feed snapshot for
  reproducibility when external data is allowed.
