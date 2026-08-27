---
name: h3-py
description: "Use Uber's h3 Python bindings for hierarchical hexagonal
  geospatial indexing, cell/grid/edge operations, polygon and GeoJSON
  conversion, and string/integer/NumPy API selection."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# h3-py

Use this skill when a task needs H3 geospatial indexing from Python: map a
latitude/longitude to a cell, inspect or navigate cells, measure spherical
quantities, index polygons, convert GeoJSON-like objects, or choose between
H3's string, integer, memoryview, and NumPy interfaces.

## Install and verify

The public distribution is `h3` and requires Python 3.10 or newer. It has no
runtime dependency for the default string or memoryview APIs:

```console
python -m pip install h3
python -c "import h3; print(h3.versions())"
```

Install the optional NumPy API explicitly when downstream code needs
`h3.api.numpy_int`:

```console
python -m pip install 'h3[numpy]'
```

For a fuller deterministic check, run the bundled helper
[check_h3_environment.py](scripts/check_h3_environment.py). Read
[installation.md](references/installation.md) for source-build, version, and
optional-dependency details. Read
[troubleshooting.md](references/troubleshooting.md) before treating an import
or input error as an H3 algorithm failure.

## Route the task

- **Point, cell, hierarchy, grid, measurement, edge, vertex, or local-IJ work:**
  read [core-indexing](sub-skills/core-indexing/SKILL.md).
- **Polygon, hole, multipolygon, GeoJSON, `__geo_interface__`, or CRS work:**
  read [polygon-geospatial](sub-skills/polygon-geospatial/SKILL.md).
- **String versus integer indexes, NumPy arrays, memoryview buffers,
  conversions, or API performance trade-offs:** read
  [api-variants](sub-skills/api-variants/SKILL.md).

A task can use multiple routes. For example, index a polygon with
`polygon-geospatial`, then use `core-indexing` to inspect or compact the
returned cells; choose `api-variants` only at a representation boundary.

## Shared operating contract

1. Treat geographic pairs as `(lat, lng)` in degrees for H3 calls. GeoJSON
   positions are `(lng, lat)` and must be swapped exactly once at the boundary.
2. Make the resolution explicit. H3 resolutions are integers `0..15`; larger
   values represent finer cells.
3. Validate the kind of every index before passing it to an operation. A cell,
   directed edge, and vertex are different H3 index types.
4. Do not assume enumeration order. Normalize unordered cell, edge, vertex, or
   pentagon results before comparison or serialization.
5. Record package version, API variant, resolution, coordinate order, units,
   and containment mode when a result must be reproducible.
6. Keep the original repository out of runtime workflows; use only the
   references and safe helpers bundled in this skill.

## High-value entry points

- `h3.latlng_to_cell(lat, lng, res)` creates a cell from a point.
- `h3.cell_to_latlng`, `cell_to_boundary`, `cell_area`, and
  `great_circle_distance` recover geometry or measurements.
- `h3.cell_to_parent`, `cell_to_children`, `compact_cells`, and
  `uncompact_cells` handle hierarchy.
- `h3.grid_disk`, `grid_ring`, `grid_distance`, and `grid_path_cells` handle
  neighborhood and path operations.
- `h3.LatLngPoly`, `h3.h3shape_to_cells`, `h3.geo_to_cells`, and
  `h3.cells_to_geo` handle polygon workflows.
- `h3.versions()` reports the Python wrapper and wrapped C library versions;
  their major and minor versions should match.

The route-specific references contain signatures, output types, recipes, and
failure recovery. Do not infer a missing argument or unit from a neighboring
H3 language binding.
