---
name: core-indexing
description: "Use the default h3 string API for point indexing, cell inspection,
  hierarchy, grid navigation, edges, vertices, local IJ coordinates,
  measurements, and H3 index validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Core H3 indexing

Use this route when a user needs to turn a latitude/longitude into an H3 cell,
inspect a cell or index, move through the hierarchy or neighboring grid, create
edges or vertices, use local IJ coordinates, measure spherical quantities, or
validate inputs. The public default is the `h3` string API: scalar indexes are
canonical lowercase hexadecimal strings and collections are ordinary Python
lists unless a function documents an unordered result.

- Coordinate order is always `(lat, lng)` (latitude first, in degrees).
- H3 resolutions are integers `0..15`; a larger resolution is finer.
- Validate a cell/index before expensive navigation or measurement. Predicates
  return `False` for malformed or wrong-kind values; operational functions
  raise an H3 exception instead of silently accepting them.
- Outputs from grid, child, compact, pentagon, and edge enumerations have no
  guaranteed order unless stated otherwise. Compare them as sets when order is
  not part of the task.
- For representation, performance, NumPy/memoryview choices, or integer API
  calls, use [api-variants](../api-variants/SKILL.md); this route stays with
  default string behavior.
- For polygon/GeoJSON shape construction or shape-to-cells, use
  [polygon-geospatial](../polygon-geospatial/SKILL.md).
- See the [root h3-py route](../../SKILL.md) for installation and global
  routing guidance.

## Standard operating procedure

1. Normalize the task: point(s), target resolution, cell(s), requested relation,
   measurement unit, and expected output shape.
2. Use `latlng_to_cell(lat, lng, res)` for a point, then check
   `is_valid_cell(cell)` and `get_resolution(cell)`.
3. Before hierarchy/grid calls, require cells at the intended resolution and
   verify that requested parent/child resolutions are legal. For a collection,
   inspect every member; `compact_cells` requires one common resolution.
4. Use the smallest operation that matches the task: `grid_disk` for filled
   neighborhoods, `grid_ring` for an exact shell, `grid_path_cells` for an
   ordered shortest path, and `grid_distance` for a scalar distance.
5. For a directed edge, confirm `are_neighbor_cells(origin, destination)` or
   catch `H3NotNeighborsError`; validate the resulting edge separately.
6. For vertices, use `cell_to_vertexes` rather than assuming six vertices;
   pentagons have five. For local IJ, keep one origin and the same resolution.
7. Measure with explicit units (`km`, `m`, `rads`; areas use `km^2`, `m^2`,
   `rads^2`) when output leaves the immediate call site.
8. Record the API call, resolution, coordinate order, unit, and any caught
   exception so a result can be reproduced without the source checkout.

## Quick checks

```python
import h3

cell = h3.latlng_to_cell(37.7752702151959, -122.418307270836, 9)
assert cell == "8928308280fffff"
assert h3.is_valid_index(cell) and h3.is_valid_cell(cell)
assert h3.get_resolution(cell) == 9
assert h3.cell_to_latlng(cell)[0] == 37.77670234943567
```

For a deterministic package check, run the bundled helper:

```console
python scripts/smoke_core.py --help
python scripts/smoke_core.py check
```

Read [api-reference.md](references/api-reference.md) for the supported surface,
[workflows.md](references/workflows.md) for copyable recipes, and
[troubleshooting.md](references/troubleshooting.md) before retrying a failure.

## Acceptance checklist

- [ ] The input uses `(lat, lng)`, not `(lng, lat)`.
- [ ] Every cell/edge/vertex passed to an operation has the correct kind and
      passes its corresponding `is_valid_*` predicate.
- [ ] Resolution transitions are monotonic and within `0..15`.
- [ ] Grid/path operations use same-resolution cells and an affordable `k`.
- [ ] Collections are not accidentally supplied as one string.
- [ ] A unit is valid for the requested quantity and is stated in the result.
- [ ] Pentagon behavior is accounted for where a fixed six-neighbor or
      six-vertex assumption would be unsafe.
- [ ] Unordered output is normalized before comparison or serialization.

## Failure recovery

- `H3CellInvalidError`, `H3IndexInvalidError`, or a `False` predicate result:
  stop and repair the index source; do not coerce a random hexadecimal string.
- `H3ResDomainError` or `H3ResMismatchError`: inspect both resolutions and
  choose a parent/child target in range; grid paths and local IJ require the
  same resolution.
- `H3NotNeighborsError`: test adjacency and reverse the edge direction only
  when the requested direction is actually intended.
- `H3FailedError` during distance/local IJ/path: reduce the geographic span or
  choose a known same-face neighborhood; the operation can be undefined or
  too far to compute, not evidence that the indexes are invalid.
- `ValueError` for a unit: use only the documented units in
  [api-reference.md](references/api-reference.md).
- Import or missing-package failures: follow the root installation route, then
  rerun `smoke_core.py check` before diagnosing H3 data.
