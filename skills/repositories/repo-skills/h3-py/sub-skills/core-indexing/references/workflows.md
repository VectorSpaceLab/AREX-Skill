# Core indexing workflows

All examples use the default string API (`import h3`). They use latitude first,
longitude second and are deterministic apart from documented unordered list
ordering. Add `sorted(...)` when serializing or comparing unordered results.

## Point to cell and inspect it

```python
import h3

lat, lng, res = 37.7752702151959, -122.418307270836, 9
cell = h3.latlng_to_cell(lat, lng, res)
assert cell == "8928308280fffff"
assert h3.is_valid_cell(cell)
assert h3.get_resolution(cell) == res

center = h3.cell_to_latlng(cell)       # (lat, lng), degrees
boundary = h3.cell_to_boundary(cell)   # tuple[(lat, lng), ...]
assert len(boundary) in (5, 6)
print(cell, center, boundary)
```

Use `get_resolution`, `is_pentagon`, `get_base_cell_number`,
`get_index_digit`, `is_res_class_III`, and `get_icosahedron_faces` for
inspection. `get_res0_cells()` enumerates the 122 resolution-0 cells;
`get_pentagons(res)` enumerates the 12 pentagons at one resolution.

## Validate before processing a collection

```python
cells = [
    h3.latlng_to_cell(37.775, -122.418, 9),
    h3.latlng_to_cell(37.776, -122.417, 9),
]

if not all(h3.is_valid_cell(c) for c in cells):
    raise ValueError("input contains a non-cell H3 index")
resolutions = {h3.get_resolution(c) for c in cells}
if len(resolutions) != 1:
    raise ValueError("this workflow requires one resolution")

# `is_valid_index` is broader: it also accepts edge and vertex indexes.
assert all(h3.is_valid_index(c) for c in cells)
```

Use `is_valid_directed_edge` and `is_valid_vertex` for those distinct index
kinds. Predicates are good gates; an operation can still reject a valid index
of the wrong kind or a mismatched resolution.

## Walk the hierarchy

```python
import h3

child = h3.latlng_to_cell(37.775, -122.418, 9)
parent = h3.cell_to_parent(child, 8)
assert h3.get_resolution(parent) == 8
assert h3.cell_to_parent(child) == h3.cell_to_parent(child, 8)

children = h3.cell_to_children(parent, 9)
assert child in children
assert len(children) == h3.cell_to_children_size(parent, 9)
assert h3.cell_to_center_child(parent, 9) in children

# Position APIs round-trip when the parent/child resolutions are coherent.
pos = h3.cell_to_child_pos(child, 8)
assert h3.child_pos_to_cell(parent, 9, pos) == child
```

A parent target must not be finer than its cell; a child target must not be
coarser or exceed resolution 15. At resolution 0 there is no coarser parent.
At resolution 15 there is no finer child. Pentagon topology can make child
counts differ from the usual seven-child hexagon expectation.

## Compact and uncompact a complete sibling group

```python
import h3

parent = h3.cell_to_parent(
    h3.latlng_to_cell(37.775, -122.418, 9),
    8,
)
children = h3.cell_to_children(parent, 9)
compact = h3.compact_cells(children)
assert parent in compact

expanded = h3.uncompact_cells(compact, 9)
assert set(expanded) == set(children)
assert all(h3.get_resolution(c) == 9 for c in expanded)
```

`compact_cells` is not a generic deduplicator: all input cells must be valid,
unique, and at one resolution, and only complete child groups can collapse.
Pass a list/set/generator of cells, not a single string (a string is iterable by
characters). `uncompact_cells(cells, target_res)` returns only the requested
resolution and rejects a target coarser than any input.

## Grid disk, ring, distance, and path

```python
import h3

start = h3.latlng_to_cell(37.775, -122.418, 9)
disk = h3.grid_disk(start, 2)    # includes start; unordered
ring = h3.grid_ring(start, 1)    # exact distance 1; unordered
assert start in disk
assert set(ring).issubset(set(disk))
assert all(h3.grid_distance(start, c) == 1 for c in ring)

neighbor = next(iter(ring))
assert h3.are_neighbor_cells(start, neighbor)
path = h3.grid_path_cells(start, neighbor)
assert path[0] == start and path[-1] == neighbor
assert len(path) == h3.grid_distance(start, neighbor) + 1
```

`k` must be nonnegative. A pentagon can have five ring-1 neighbors. Grid path
selection is minimum length but not unique; test endpoints and adjacency rather
than a particular valid path unless the application requires a fixed one. Keep
both cells at the same resolution. Long or face-crossing distances can raise
`H3FailedError` even when both cells are valid.

## Directed edge from adjacent cells

```python
import h3

origin = h3.latlng_to_cell(37.775, -122.418, 9)
destination = next(iter(h3.grid_ring(origin, 1)))
assert h3.are_neighbor_cells(origin, destination)

edge = h3.cells_to_directed_edge(origin, destination)
assert h3.is_valid_directed_edge(edge)
assert h3.directed_edge_to_cells(edge) == (origin, destination)
assert h3.get_directed_edge_origin(edge) == origin
assert h3.get_directed_edge_destination(edge) == destination
assert len(h3.directed_edge_to_boundary(edge)) == 2
```

The reverse direction is a different edge. `origin_to_directed_edges(origin)`
returns all outgoing edges (normally six for a hexagon and five for a pentagon).
If cells are not adjacent, catch `H3NotNeighborsError` instead of constructing a
fake edge.

## Vertices and vertex coordinates

```python
import h3

cell = h3.latlng_to_cell(37.775, -122.418, 9)
vertices = h3.cell_to_vertexes(cell)
assert len(vertices) == (5 if h3.is_pentagon(cell) else 6)
assert all(h3.is_valid_vertex(v) for v in vertices)
coords = [h3.vertex_to_latlng(v) for v in vertices]
assert all(len(pair) == 2 for pair in coords)

# Use a checked range; pentagons have no vertex number 5.
first = h3.cell_to_vertex(cell, 0)
assert first == vertices[0]
```

## Local IJ round trip in a local domain

```python
import h3

origin = h3.latlng_to_cell(0.0, 0.0, 9)
neighbor = next(iter(h3.grid_ring(origin, 1)))
i, j = h3.cell_to_local_ij(origin, neighbor)
recovered = h3.local_ij_to_cell(origin, i, j)
assert recovered == neighbor
```

The origin cell does not necessarily have IJ coordinates `(0, 0)`; the
coordinate system is anchored to the origin's base-cell center. Use one origin,
one resolution, and nearby cells. Catch `H3FailedError` for a coordinate outside
the local domain or a face-crossing conversion.

## Measurements with explicit units

```python
import h3

cell = h3.latlng_to_cell(37.775, -122.418, 9)
edge = next(iter(h3.origin_to_directed_edges(cell)))

area_km2 = h3.cell_area(cell, unit="km^2")
edge_m = h3.edge_length(edge, unit="m")
distance_km = h3.great_circle_distance(
    (45.7597, 4.8422), (48.8567, 2.3508), unit="km"
)
avg_area = h3.average_hexagon_area(9, unit="km^2")
avg_edge = h3.average_hexagon_edge_length(9, unit="km")
assert all(x > 0 for x in (area_km2, edge_m, distance_km, avg_area, avg_edge))
```

Valid area units are `km^2`, `m^2`, and `rads^2`; valid length/distance units
are `km`, `m`, and `rads`. Average hexagon values exclude pentagons and are not
the area or perimeter of a particular cell.
