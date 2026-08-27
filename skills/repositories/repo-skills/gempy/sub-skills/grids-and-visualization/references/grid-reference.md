# Grid reference

Read this when a task depends on exact grid shapes, active-grid semantics, or
public setter signatures. The facts below are distilled from GemPy's public
API and live package inspection; the original checkout is not required.

## Coordinate and shape contract

A model extent is a six-value sequence in this exact order:

```text
[x_min, x_max, y_min, y_max, z_min, z_max]
```

A dense regular-grid resolution is `[n_x, n_y, n_z]`. A `RegularGrid` creates
`n_x * n_y * n_z` cell-center coordinates. Along each axis, centers are
uniformly spaced by `(max - min) / n`; the first center is one half-cell from
that axis minimum and the last is one half-cell from its maximum. For example,
`extent=[0, 10, 0, 20, 0, 30]` and `resolution=[2, 4, 6]` gives spacings
`(5, 5, 5)` and first center `(2.5, 2.5, 2.5)`. `regular_grid.values` is
`(n_x*n_y*n_z, 3)` in the meshgrid order used by GemPy. Custom coordinates are
world XYZ points, not integer cell indices.

`RegularGrid.values_vtk_format` is a separate corner-coordinate representation
with resolution one larger on each axis; use it only for VTK-style geometry,
not as the model's cell-center array. A regular-grid `extent` and `resolution`
can be inspected directly:

```python
rg = model.grid.regular_grid
assert rg.extent.shape == (6,)
assert rg.resolution.shape == (3,)
print(rg.dx, rg.dy, rg.dz)
print(rg.x_coord, rg.y_coord, rg.z_coord)
```

Model construction with `resolution=[...]` selects a dense regular grid. Model
construction without a resolution initializes an octree grid using the
refinement level. Do not assume an octree's point count or ordering is the
same as a dense block.

## Public grid objects and setters

| Public API | Input contract | Result and important side effect |
|---|---|---|
| `Grid(extent=None, resolution=None)` | Optional extent and `[nx, ny, nz]` | Empty container, or a dense grid when both are supplied |
| `Grid.init_dense_grid(extent, resolution)` | Six extent values and three resolution values | New `Grid` with `DENSE` active |
| `Grid.init_octree_grid(extent, octree_levels, base_resolution=None, legacy=False)` | Extent, levels, optional base resolution | New `Grid` with `OCTREE` active; base resolution is derived if omitted |
| `gp.set_custom_grid(grid, xyz_coord, reset=False)` | Numeric `(n, 3)` XYZ array | Stores `CustomGrid`; activates `CUSTOM`; `reset=True` selects only custom plus GemPy's sentinel flag |
| `gp.set_section_grid(grid, section_dict)` | Name → `((x0,y0),(x1,y1),(nu,nz))` | Creates or replaces `Sections`; activates `SECTIONS` |
| `gp.set_centered_grid(grid, centers, resolution, radius)` | `(n,3)` centers, three resolution values, scalar or three radii | Stores a centered-grid object and activates `CENTERED` |
| `gp.set_active_grid(grid, grid_type, reset=False)` | List of `Grid.GridTypes` flags | ORs flags into the selection, or starts from the sentinel when reset |
| `gp.compute_model_at(model, at, engine_config=None, skip_validation=False)` | `(n,3)` XYZ query points | Computes and returns `solutions.raw_arrays.custom`; resets the model to a custom active grid |

`set_custom_grid` converts coordinates to float64 and rejects arrays whose
second dimension is not 3. It is appropriate for borehole samples or sparse
probe coordinates. `set_centered_grid` is also a public API, but the generated
values and downstream gravity usage are owned by the advanced/geophysics route.

## Active flags and compute output

`Grid.GridTypes` is a Python `enum.Flag` with these public members:

```python
Grid.GridTypes.OCTREE       # 1
Grid.GridTypes.DENSE        # 2
Grid.GridTypes.CUSTOM       # 4
Grid.GridTypes.TOPOGRAPHY   # 8
Grid.GridTypes.SECTIONS     # 16
Grid.GridTypes.CENTERED     # 32
```

The implementation also carries `Grid.GridTypes.NONE` as a sentinel flag
(`1024` in the inspected build). Do not compare `active_grids` for exact
integer equality. Use membership or bitwise operations:

```python
active = model.grid.active_grids
if model.grid.GridTypes.CUSTOM in active:
    print(model.grid.custom_grid.length)
```

`grid.values` is rebuilt as a concatenation in this order:
`OCTREE`, `DENSE`, `CUSTOM`, `TOPOGRAPHY`, `SECTIONS`, `CENTERED`, restricted
to active and defined components. A setter activates its component but does
not clear other flags. Consequently, after adding a custom grid, a compute may
produce both the regular-grid result and `raw_arrays.custom`; after adding
sections/topography, the evaluated point count also grows. Reset the selection
explicitly when a single-grid result is required:

```python
gp.set_active_grid(model.grid,
                   [model.grid.GridTypes.DENSE],
                   reset=True)
gp.compute_model(model)
```

Keep only compatible base-grid choices active. `Grid.regular_grid` raises when
both dense and octree are active at once, because there is no single regular
grid to use for extents and slices. The sentinel `NONE` is not a real point
source.

## Section grid details

The public section dictionary is normalized to floats for endpoints and ints
for resolution. Each section requires distinct start and stop XY points. The
vertical range is taken from the selected regular grid's `extent[4:]`. Each
section contributes `n_u * n_z` points. Names are available as a NumPy array in
`model.grid.sections.names`; cumulative offsets are in `.length`; per-section
metadata is in `.df` (which requires pandas):

```python
sections = model.grid.sections
print(sections.names)
print(sections.df[["start", "stop", "resolution", "dist"]])
lo, hi = sections.get_section_args("section_SW_NE")
xyz = sections.get_section_grid("section_SW_NE")
assert xyz.shape[0] == hi - lo
```

Use names that are stable, unique, and safe to pass to the viewer. The viewer's
`section_names=[...]` refers to these names, while the special string
`"topography"` means the topographic map view, not a custom section name.

## Topography input paths

All topography paths require a defined `grid.regular_grid`; they activate the
`TOPOGRAPHY` flag. `Topography.values` is a flattened `(n, 3)` array and
`Topography.values_2d` is the source surface with shape `(n_x_topo, n_y_topo,
3)`. The topography extent is inherited from the regular grid.

### Synthetic random surface

```python
topo = gp.set_topography_from_random(
    grid=model.grid,
    fractal_dimension=1.2,
    d_z=np.array([300., 750.]),
    topography_resolution=np.array([50, 50]),
)
assert topo.values_2d.shape == (50, 50, 3)
```

`topography_resolution=None` uses the regular-grid resolution. The generated
surface uses the model extent and the random fractal generator; seed NumPy in a
caller when reproducibility matters. `d_z` is the elevation range input. The
fractal generator requires SciPy in the inspected implementation.

### XYZ vertex cloud

```python
vertices = np.asarray([
    [0., 0., 100.], [0., 100., 110.],
    [100., 0., 120.], [100., 100., 130.],
])
topo = gp.set_topography_from_arrays(model.grid, vertices)
```

The API accepts an `(n, 3)` XYZ vertex array and interpolates Z onto an XY
lattice spanning the regular-grid extent using SciPy's nearest-neighbor
`griddata` path. Verify that the cloud covers the model XY extent and that its
Z values are finite; otherwise the interpolation can contain NaN values or
produce an unrepresentative surface.

### Structured file

`gp.set_topography_from_file(grid, filepath, crop_to_extent=None)` delegates to
the optional `subsurface` structured-topography reader, then activates
`TOPOGRAPHY`. The path is a reader input, not a NumPy `.npy` shortcut. If the
reader package or format support is absent, use the array or random path rather
than importing private reader internals.

`Topography.from_arrays` and `Topography.from_subsurface_structured_data` are
public class methods useful when already holding structured arrays, but the
GemPy grid API setters are preferred. The placeholder functions
`set_topography_from_gdal()` and `set_topography_from_array()` are explicitly
unimplemented in this API version and should not be called.

## Compute-at and restoration pattern

Use this pattern when a model has an active regular grid that must remain the
main result after a point query:

```python
old_active = model.grid.active_grids
query = np.asarray([[x0, y0, z0], [x1, y1, z1]], dtype=float)
point_values = gp.compute_model_at(model, query)
# compute_model_at has reset active grids to CUSTOM.
model.grid.active_grids = old_active
# Recompute before reading regular/section/topography results again.
gp.compute_model(model)
```

The point-query return is one value per input row, in input order. Do not call
it in the middle of a workflow that assumes the previous active-grid selection
without restoring and recomputing.
