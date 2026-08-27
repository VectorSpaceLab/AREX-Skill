# Core indexing API reference

This reference describes h3-py 4.x as exposed by the default `import h3`
(string) API. The inspected package reports matching Python and C versions
(e.g. 4.5.0 in the production environment). Use lowercase hexadecimal H3
strings in examples. The default collection outputs are Python `list` objects;
several functions explicitly return unordered collections, so do not rely on
iteration order.

## Coordinate and validation conventions

- Every geographic pair is `(lat, lng)` in degrees. H3 does not use `(lng, lat)`
  for these functions. `cell_to_latlng`, `vertex_to_latlng`, and boundary
  functions return the same order.
- Valid resolutions are integer values `0` through `15`, inclusive.
- `is_valid_index(h)` accepts a valid cell, directed edge, or vertex. The more
  specific predicates distinguish the three kinds and return `False` for bad
  types or malformed strings rather than raising.
- Operational functions validate their inputs and translate H3 failures to
  public exception classes such as `H3CellInvalidError`, `H3ResDomainError`,
  `H3ResMismatchError`, `H3NotNeighborsError`, `H3DomainError`, and
  `H3FailedError`.
- Integer, NumPy, and memoryview representations are a separate API choice;
  use [api-variants](../../api-variants/SKILL.md) rather than changing types in a
  core workflow.

## API groups

| Group | Signature | Result and important assumptions |
|---|---|---|
| Point indexing | `latlng_to_cell(lat, lng, res)` | One canonical hex string for the cell containing the point at `res`. |
| Cell center | `cell_to_latlng(h)` | `(float lat, float lng)` center in degrees. |
| Cell boundary | `cell_to_boundary(h)` | Tuple of `(lat, lng)` pairs; 5 for a pentagon, normally 6 for a hexagon. |
| Cell validity | `is_valid_cell(h)` | `bool`; only a valid cell passes. |
| Any-index validity | `is_valid_index(h)` | `bool`; cell, directed edge, or vertex can pass. |
| Edge validity | `is_valid_directed_edge(edge)` | `bool`; a cell is not an edge. |
| Vertex validity | `is_valid_vertex(v)` | `bool`; a cell or edge is not a vertex. |
| Resolution | `get_resolution(h)` | `int` resolution of a valid cell/index accepted by the binding; use on cells in normal workflows. |
| Parent | `cell_to_parent(h, res=None)` | One cell at `res`; `None` means the immediate coarser parent. `res` cannot be finer than `h`. |
| Children | `cell_to_children(h, res=None)` | Unordered `list[str]` at `res`; `None` means one finer resolution. Same resolution returns `[h]`. |
| Child count | `cell_to_children_size(h, res=None)` | `int` number of children at the target resolution. |
| Center child | `cell_to_center_child(h, res=None)` | One descendant at target resolution; target must be equal or finer. |
| Child position | `cell_to_child_pos(child, res_parent)` | `int` position of a child relative to a parent resolution. |
| Child from position | `child_pos_to_cell(parent, res_child, child_pos)` | One canonical child string; inverse of `cell_to_child_pos` when resolutions are coherent. |
| Compaction | `compact_cells(cells)` | Unordered `list[str]`; combines complete sibling groups. Input cells must share one resolution. |
| Uncompaction | `uncompact_cells(cells, res)` | Unordered `list[str]`, all at `res`; `res` must be no coarser than each input cell. |
| Filled grid | `grid_disk(h, k=1)` | Unordered cells with grid distance `<= k`, including `h`; `k` must be nonnegative. |
| Hollow grid | `grid_ring(h, k=1)` | Unordered cells with grid distance `== k`; `k=0` contains `h`. |
| Grid distance | `grid_distance(h1, h2)` | Shortest graph distance as `int`; same-resolution cells required; distant cases may fail. |
| Grid path | `grid_path_cells(start, end)` | Ordered `list[str]` from start through end on a minimum-length, non-unique path; same resolution required. |
| Adjacency | `are_neighbor_cells(h1, h2)` | `bool`; true only for adjacent cells (not a cell with itself). |
| Directed edge creation | `cells_to_directed_edge(origin, destination)` | One edge string for adjacent origin/destination; raises `H3NotNeighborsError` otherwise. |
| Edge endpoints | `directed_edge_to_cells(e)` | `(origin, destination)` tuple of cell strings. |
| Edge origin | `get_directed_edge_origin(e)` | One origin cell string. |
| Edge destination | `get_directed_edge_destination(e)` | One destination cell string. |
| Origin edges | `origin_to_directed_edges(origin)` | Unordered edge strings starting at `origin`; normally 6 for a hexagon, 5 for a pentagon. |
| Edge boundary | `directed_edge_to_boundary(edge)` | Tuple of two `(lat, lng)` points describing the edge boundary. |
| One vertex | `cell_to_vertex(h, vertex_num)` | One vertex string; `vertex_num` is `0..5` for a hexagon and `0..4` for a pentagon. |
| All vertices | `cell_to_vertexes(h)` | List of 6 vertex strings for a hexagon or 5 for a pentagon. |
| Vertex coordinates | `vertex_to_latlng(v)` | `(float lat, float lng)` in degrees. |
| Local IJ forward | `cell_to_local_ij(origin, h)` | `(i, j)` integer tuple in the local coordinate system of `origin`. |
| Local IJ inverse | `local_ij_to_cell(origin, i, j)` | One cell string at the origin's resolution, when the IJ coordinate is in the valid local domain. |
| Cell area | `cell_area(h, unit='km^2')` | Spherical area as `float`; units `km^2`, `m^2`, or `rads^2`. |
| Edge length | `edge_length(e, unit='km')` | Spherical edge length as `float`; units `km`, `m`, or `rads`. |
| Point distance | `great_circle_distance(latlng1, latlng2, unit='km')` | Spherical distance as `float`; pairs are `(lat, lng)`; units `km`, `m`, or `rads`. |
| Average hex area | `average_hexagon_area(res, unit='km^2')` | `float` average for hexagons at `res`; excludes pentagons; units `km^2`, `m^2`, `rads^2`. |
| Average edge length | `average_hexagon_edge_length(res, unit='km')` | `float` average hexagon edge length; excludes pentagons; units `km`, `m`, `rads`. |

## Cell and index properties

```python
h3.get_res0_cells()                  # unordered list[str], 122 cells
h3.get_pentagons(res)                # unordered list[str], 12 cells
h3.get_num_cells(res)                # int, pentagons included
h3.is_pentagon(cell)                 # bool
h3.is_res_class_III(cell)            # bool; odd resolutions are Class III
h3.get_base_cell_number(cell)        # int, 0..121
h3.get_index_digit(cell, res)        # int digit at 1-based resolution
h3.get_icosahedron_faces(cell)       # set[int], face numbers 0..19
h3.deconstruct_cell(cell)             # [base_cell, digit1, ..., digitN]
h3.construct_cell(base_cell, *digits, res=None)  # cell string
```

`get_index_digit` uses a 1-based digit resolution and is invalid for `0` or a
value beyond the supported index. `construct_cell` requires base-cell number
`0..121`, digits `0..6`, at most 15 digits, and `res` equal to the number of
digits if supplied. Pentagon base cells can reject a deleted leading digit.
`construct_cell`/`deconstruct_cell` are useful for inspection and exact
round-trips, not for inventing geographic cells.

## Resolution and collection rules

A child target must satisfy `resolution(parent) <= target <= 15`; a parent target
must satisfy `0 <= target <= resolution(cell)`. `cell_to_children_size` counts
all descendants at the requested target, including the pentagon topology rules.
For `compact_cells`, pass an iterable of cells—not a single string—and ensure
the cells are valid, unique, and at one resolution. Compaction only replaces a
complete set of children with its parent; it is not a geometric simplifier.
`uncompact_cells` expands to exactly one target resolution and rejects malformed,
mixed-invalid, or coarser targets.

## Grid, edge, vertex, and local IJ rules

Grid operations use cells at one resolution. A disk includes its center; a ring
does not include the center except at `k=0`. Pentagon neighborhoods can have
five rather than six neighbors. `grid_path_cells` is ordered but not unique, so
only assert endpoints, adjacency, and length unless a particular path is part
of the contract. `grid_distance` can raise `H3FailedError` for valid cells too
far apart for the underlying navigation algorithm.

Directed edges are directional: `cells_to_directed_edge(a, b)` is different from
`cells_to_directed_edge(b, a)`. Create one only after checking adjacency. A
hexagon has six outgoing edges and a pentagon five. Vertices are also a distinct
index kind; do not pass a vertex where a cell is required.

Local IJ coordinates are local, face/domain-limited coordinates at the origin's
resolution. `(0, 0)` is not guaranteed to be the origin cell's coordinates; it
is tied to the center of the origin's base cell. Round trips are safe for cells
returned by `cell_to_local_ij` while they remain in the same valid local domain.
Crossing an icosahedron face or requesting an unreachable coordinate can raise
`H3FailedError`.
