# Core indexing troubleshooting

## Install and import

**Symptom:** `ModuleNotFoundError: No module named 'h3'`, an unexpected package
version, or `import h3` fails before any API call.

1. Install the public package in the active environment:

   ```console
   python -m pip install h3
   # or: conda install -c conda-forge h3-py
   ```

2. Check that the interpreter and package agree:

   ```console
   python -c "import h3; print(h3.__version__, h3.versions())"
   ```

3. If the import still fails, check for a local file or directory named `h3`
   shadowing the installed package and use the intended interpreter. Do not
   mix the default string route with another API's scalar/collection types;
   representation choices belong in [api-variants](../../api-variants/SKILL.md).

`h3.versions()` returns `{'c': 'X.Y.Z', 'python': 'A.B.Z'}`. Major and minor
versions are intended to match; a patch difference is allowed by the package's
versioning contract.

## Invalid indexes and validation

**Symptoms:** `False` from a predicate, `H3CellInvalidError`,
`H3IndexInvalidError`, `H3DirEdgeInvalidError`, or `H3VertexInvalidError`.

- A canonical cell is a lowercase hexadecimal string such as
  `8928308280fffff`; a plausible-looking string can still have invalid mode,
  reserved bits, digits, or resolution.
- `is_valid_cell(h)` is the gate for cell operations;
  `is_valid_directed_edge(e)` and `is_valid_vertex(v)` are distinct gates.
  `is_valid_index(x)` is the broad gate for any of the three kinds.
- A valid edge or vertex is not a valid cell. Do not call `cell_to_latlng` or
  `cell_to_parent` on an edge/vertex.
- Predicates intentionally return `False` for malformed Python values. Other
  operations should be allowed to raise the informative H3 exception; do not
  catch and replace it with a guessed result.

Example gate:

```python
if not h3.is_valid_cell(cell):
    raise ValueError(f"not a valid H3 cell: {cell!r}")
resolution = h3.get_resolution(cell)
```

## Invalid resolution or resolution mismatch

**Symptoms:** `H3ResDomainError` or `H3ResMismatchError` from parent, children,
center child, compact/uncompact, grid path, or another navigation call.

- Keep resolutions in `0..15`.
- `cell_to_parent(cell, target)` requires `target <= resolution(cell)`;
  `cell_to_parent(cell)` on a resolution-0 cell has no valid target.
- `cell_to_children(cell, target)` and `cell_to_center_child` require
  `target >= resolution(cell)` and no greater than 15. The default child target
  is one finer resolution.
- `uncompact_cells(cells, target)` cannot expand to a coarser target than the
  input cells. It returns every result at exactly `target`.
- `grid_distance` and `grid_path_cells` require same-resolution cells. Normalize
  to a common resolution first; do not compare a parent and child as neighbors.

Check before the call:

```python
rs = [h3.get_resolution(c) for c in cells]
assert len(set(rs)) == 1
assert 0 <= target <= 15
```

## Mixed-resolution, duplicate, or wrong collection input

**Symptoms:** `H3ResMismatchError`, `H3DuplicateInputError`,
`H3CellInvalidError`, or an opaque failure from a collection operation.

`compact_cells` expects an iterable of valid, unique cells all at one input
resolution. It only collapses complete sibling groups. `uncompact_cells` expects
an iterable too; passing one string makes Python iterate its characters, not the
index as one cell. Use `[cell]` for a one-cell collection. Validate and inspect
resolutions before calling either function.

Do not use `set` ordering as a result contract. Normalize only for comparison:
`set(output)`, `sorted(output)`, or a stable application-specific key.

## Invalid units or wrong measurement quantity

**Symptom:** `ValueError` from an area, length, or distance function.

Use exactly:

- `cell_area` and `average_hexagon_area`: `km^2`, `m^2`, `rads^2`.
- `edge_length`, `great_circle_distance`, and
  `average_hexagon_edge_length`: `km`, `m`, `rads`.

The default area unit is `km^2`; the default length/distance unit is `km`.
`rads`/`rads^2` are spherical angular units, not kilometers. State units in
serialized results and do not mix area and length conversions.

## Grid navigation and distance failures

**Symptoms:** `H3FailedError`, `H3GridNavigationError`, or an unexpectedly large
result from `grid_disk`.

- Validate the center cell and use a nonnegative integer `k`.
- A disk includes the center and grows with `k`; a ring contains only the exact
  shell. Results are unordered. Pentagon centers have five immediate neighbors.
- `grid_distance` is a graph distance, not a spherical kilometer distance.
  Use `great_circle_distance` for coordinate distance.
- The implementation may fail to compute a very distant valid-cell distance or
  path. Reduce the span, split the work into local regions, or use another
  application-level route strategy; do not infer that the cells are invalid.
- For paths, verify same resolution and expect a minimum-length but non-unique
  path. Only require a specific sequence if the application defines a tie-break.

## Directed-edge misuse

**Symptoms:** `H3NotNeighborsError`, edge validation is false, or endpoint
round-tripping does not match.

`cells_to_directed_edge(origin, destination)` is directional and only accepts
adjacent cells. Check `are_neighbor_cells` first and then assert:

```python
edge = h3.cells_to_directed_edge(origin, destination)
assert h3.directed_edge_to_cells(edge) == (origin, destination)
```

A cell with itself, a non-neighbor, a different-resolution cell, or a vertex
is not a valid edge input. Use `origin_to_directed_edges` when all outgoing
edges are needed; it returns five for pentagons and normally six for hexagons.

## Pentagon and domain errors

**Symptoms:** `H3DomainError`, `H3PentagonError`, or assumptions about six
neighbors/vertices fail.

H3 has 12 pentagons at every resolution. Detect them with `is_pentagon(cell)`.
A pentagon has five boundary vertices and five outgoing directed edges; its
neighborhood and child topology need not match a hexagon's counts. For
`cell_to_vertex(cell, vertex_num)`, valid numbers are `0..4` for pentagons and
`0..5` for hexagons. An out-of-range number raises a domain error.

A local IJ conversion or grid operation can also fail at an icosahedron face or
local coordinate domain boundary. Use `get_icosahedron_faces` for inspection,
keep local-IJ work nearby, and catch `H3FailedError` rather than fabricating an
IJ coordinate.

## Local IJ failures

**Symptoms:** `cell_to_local_ij` or `local_ij_to_cell` raises
`H3FailedError`, or a round trip returns an unexpected cell.

Local IJ is not a global coordinate system. Both cells must be at the origin's
resolution, and the destination must lie in a computable local domain. The
origin cell itself need not be `(0, 0)` because coordinates are anchored to its
base-cell center. Round-trip only coordinates produced by
`cell_to_local_ij(origin, destination)` and only while the conversion remains
in-domain.

## Coordinate and API misuse

**Symptoms:** a valid-looking result appears in the wrong region or type errors
occur around collections.

- Swap `(lng, lat)` to `(lat, lng)` before calling core geographic functions;
  polygon/GeoJSON interfaces have their own boundary documented by
  [polygon-geospatial](../../polygon-geospatial/SKILL.md).
- Use degrees for coordinates; units apply to measurements, not input pairs.
- Use `cell_to_latlng` for a center, `cell_to_boundary` for a perimeter, and
  `directed_edge_to_boundary` for one edge; do not treat a center as a polygon.
- Keep the default route's string indexes and Python lists. For integer or
  array APIs, follow [api-variants](../../api-variants/SKILL.md) instead of
  manually converting only some arguments.
- A grid ring/disk and child/compact output is unordered. A grid path is ordered.
  Respect that distinction in tests and downstream serialization.
