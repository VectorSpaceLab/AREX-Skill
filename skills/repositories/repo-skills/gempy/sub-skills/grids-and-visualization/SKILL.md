---
name: grids-and-visualization
description: "Enables GemPy grid selection, coordinate evaluation, topography
  and section setup, and optional 2-D or 3-D visual inspection of computed
  geological models."
disable-model-invocation: true
metadata:
  disco-role: operating
license: EUPL 1.2
---

# Grids and visualization

Use this route when the task is to choose where GemPy evaluates a model, query
specific coordinates, add sections or topography, or inspect an already-built
model. The model must already have valid extents and structural data; route
model creation, input tables, and compute ordering to the modeling/data
sub-skills. This route does not own mesh extraction, topology, gravity, or model
persistence.

## Fast route

1. Inspect the existing grid before changing it:

   ```python
   grid = model.grid
   print(grid.active_grids)
   print(grid.extent)                         # [xmin, xmax, ymin, ymax, zmin, zmax]
   print(grid.values.shape)
   if grid.regular_grid is not None:
       print(grid.regular_grid.resolution)
   ```

2. Choose one or more grid types and configure them **before**
   `gempy.compute_model(model)`. Grid setters activate their new grid, but do
   not remove previously active grids unless `reset=True` is used.
3. Recompute after any grid change. Results for custom, section, topography,
   and centered points are not populated by merely constructing the grid.
4. Validate shape and active flags before plotting. Run the safe bundled check
   for a package/import/grid-only diagnostic:
   [`scripts/grid_smoke.py`](scripts/grid_smoke.py).
5. Use `gempy_viewer.plot_2d` or `plot_3d` only when the optional viewer and
   its rendering dependencies are available. Use `show=False` for compositing
   or headless-friendly construction; use `image=True` for an off-screen 3-D
   render. Route installation/display failures to the environment and
   troubleshooting sub-skill.

For detailed signatures and coordinate conventions read
[`references/grid-reference.md`](references/grid-reference.md). For plotting
recipes read [`references/visualization-workflows.md`](references/visualization-workflows.md).
For failures read [`references/troubleshooting.md`](references/troubleshooting.md).

## Select a grid

- **Dense regular grid:** pass `resolution=[nx, ny, nz]` when creating the
  model. `model.grid.regular_grid` is the `RegularGrid`; its `values` are
  cell-center coordinates and normally contain `nx * ny * nz` points.
- **Octree grid:** creation with no explicit resolution uses the model's octree
  grid and refinement options. Do not assume its point count is a dense
  `nx * ny * nz` block. This route only inspects/selects it; octree tuning and
  mesh work belong to modeling/advanced routes.
- **Custom grid:**

  ```python
  import numpy as np
  import gempy as gp

  query_xyz = np.asarray([[1000., 1000., 700.],
                          [1000., 1000., 400.]], dtype=float)
  gp.set_custom_grid(model.grid, query_xyz)
  gp.compute_model(model)
  values = model.solutions.raw_arrays.custom
  ```

  `query_xyz` must be an `(n, 3)` array in the same world coordinate system as
  the model extent. Returned custom values preserve the input row order.
- **Centered grid:** use `gp.set_centered_grid(grid, centers, resolution,
  radius)` for points concentrated around one or more centers. `centers` is
  `(n, 3)`; `resolution` is a three-component sequence; `radius` is a scalar
  or three-component sequence. This route configures the grid only; gravity
  kernels and geophysical inputs belong to the advanced route.

## Sections and topography

A section dictionary maps each stable section name to
`((x_start, y_start), (x_stop, y_stop), (n_horizontal, n_vertical))`:

```python
gp.set_section_grid(model.grid, {
    "section_SW_NE": ((250., 250.), (1750., 1750.), (100, 80)),
    "section_NW_SE": ((250., 1750.), (1750., 250.), (100, 80)),
})
```

The endpoints are world X/Y coordinates; the section spans the regular grid's
Z extent. Names are retained in insertion order and are the names passed to
`plot_2d(..., section_names=[...])`. Inspect `model.grid.sections.df`,
`.names`, `.resolution`, and `.get_section_grid(name)` before plotting.

Topography APIs are:

- `gp.set_topography_from_random(grid, fractal_dimension=2.0, d_z=None,
  topography_resolution=None)` for a synthetic surface. A supplied resolution
  should be `[nx, ny]` with values at least 2; `d_z` controls the elevation
  range. It uses the model XY extent and activates `TOPOGRAPHY`.
- `gp.set_topography_from_arrays(grid, xyz_vertices)` for an `(n, 3)` XYZ
  vertex cloud. GemPy interpolates those vertices onto the regular grid's XY
  lattice; this path requires SciPy.
- `gp.set_topography_from_file(grid, filepath, crop_to_extent=None)` for a
  structured topography reader. This path requires the optional `subsurface`
  package and a reader-supported file. Do not use the unimplemented GDAL or
  singular-array stubs as a fallback.

Topography and sections are grid data, not merely viewer overlays. Activate
both before computing when their results are needed. Plot a geological map with
`section_names=["topography"]` after topography has been configured and the
model has been computed.

## Active-grid discipline

`Grid.GridTypes` is a flag set: `OCTREE`, `DENSE`, `CUSTOM`, `TOPOGRAPHY`,
`SECTIONS`, and `CENTERED`. `gp.set_active_grid(grid, grid_type=[...],
reset=False)` ORs requested flags into the current set. Use `reset=True` to
replace the active selection deliberately:

```python
# Keep only the dense grid for a baseline recomputation.
gp.set_active_grid(model.grid, [model.grid.GridTypes.DENSE], reset=True)

# Add a section and topography to the currently selected base grid.
gp.set_active_grid(model.grid,
                   [model.grid.GridTypes.DENSE,
                    model.grid.GridTypes.SECTIONS,
                    model.grid.GridTypes.TOPOGRAPHY],
                   reset=True)
```

Do not infer the result array from the last setter. `grid.values` is a
concatenation of every active grid's coordinates, and a compute call evaluates
all of them. Before and after a compute, log `active_grids`, each component's
length, and the relevant `solutions.raw_arrays` member. If a prior custom or
section grid remains active, a dense-shaped result can be unexpectedly longer
than the dense grid alone. Always recompute after resetting flags.

## Evaluate arbitrary coordinates

For a one-off coordinate evaluation, use `gp.compute_model_at(model, at)` with
an `(n, 3)` NumPy array. It returns the computed values for those rows, but
intentionally installs a custom grid, resets the active selection to `CUSTOM`,
and computes the model. Save `old_flags = model.grid.active_grids` before the
call and restore them afterward with `model.grid.active_grids = old_flags` (or
an explicit `set_active_grid(..., reset=True)`), then recompute if subsequent
work expects the old grid solutions. This side effect is part of the public
API; do not treat `compute_model_at` as a read-only probe.

## Viewer boundary

`gempy_viewer` is optional from this route's perspective. A 2-D plot uses
Matplotlib and can return a `Plot2D` object whose `.axes` can be customized;
3-D plotting returns a viewer object wrapping a PyVista plotter. Viewer calls
require a computed model for lithology/scalar results, while input-only views
may be useful before computation. See the visualization reference for
`direction`, `position`, `cell_number`, named sections, scalar fields,
headless construction, and output expectations.
