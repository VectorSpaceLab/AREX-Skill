# Grid and visualization troubleshooting

Use this page when grid construction or viewer inspection fails. Keep model
creation and structural-data validation with the modeling/data routes; this
page covers grid state, optional dependencies, and display boundaries.

## The import fails before a grid exists

**Symptom:** `import gempy` raises a missing `gempy_engine` or another required
package error.

**Cause:** GemPy's core API imports its computational engine. A viewer package
alone is not enough.

**Recovery:** Use the environment-and-troubleshooting route to install GemPy's
normal runtime requirements, then rerun the bundled display-free check:

From the generated GemPy skill root, run:

```bash
python sub-skills/grids-and-visualization/scripts/grid_smoke.py --json
```

Do not work around the error by importing private grid modules from a partial
installation. The smoke helper should report a concise missing-environment
message and exit non-zero.

## `regular_grid` is missing or raises because both base grids are active

**Symptom:** `model.grid.regular_grid` is `None`, or raises an error stating
that dense and octree grids are both active.

**Likely causes:** The model was created without a dense resolution, or code
manually activated both `DENSE` and `OCTREE`. The `regular_grid` property is
intentionally singular because viewers and topography need one base extent.

**Recovery:** Inspect `model.grid.active_grids` and choose the intended base
selection. For a dense baseline, create the model with an explicit resolution
or reset to a defined dense component:

```python
gp.set_active_grid(model.grid, [model.grid.GridTypes.DENSE], reset=True)
```

For an octree model, leave `OCTREE` active and use its `extent` and
`regular_grid` only when the API exposes one unambiguously. Do not activate
both base choices merely to increase point count.

## Compute output contains unexpected extra points

**Symptom:** A result is longer than `nx * ny * nz`, or a later plot includes
old custom/section/topography values.

**Cause:** `set_custom_grid`, `set_section_grid`, and topography setters activate
their flags without clearing existing active flags. `Grid.values` concatenates
all active components.

**Recovery:** Log the flags and component lengths, select the desired set with
`reset=True`, and recompute:

```python
print(model.grid.active_grids)
gp.set_active_grid(
    model.grid,
    [model.grid.GridTypes.DENSE, model.grid.GridTypes.SECTIONS],
    reset=True,
)
gp.compute_model(model)
```

If a single-grid result is expected, assert the active flags before reading
`solutions.raw_arrays`. Do not assume the most recently configured grid owns
all output.

## `compute_model_at` changes later plots or solutions

**Symptom:** A point query succeeds, but subsequent reads or plots show only
custom points, or regular-grid output is absent.

**Cause:** `gp.compute_model_at(model, at)` is explicitly stateful. It calls
`set_custom_grid(..., reset=True)`, computes, and returns
`solutions.raw_arrays.custom`.

**Recovery:** Save the active flags before the query, restore them after it,
and recompute the intended grid:

```python
old_active = model.grid.active_grids
point_values = gp.compute_model_at(model, query_xyz)
model.grid.active_grids = old_active
gp.compute_model(model)
```

Also verify that `query_xyz.shape == (n, 3)` and that rows are in the desired
world-coordinate order.

## Section setup fails or the section is absent from the viewer

**Symptom:** `set_section_grid` rejects the input, produces no points, or
`plot_2d(..., section_names=[name])` cannot find the name.

**Likely causes:** The dictionary shape is wrong; the two endpoints are equal;
resolution is not a two-integer pair; the name was mistyped; or the section was
added after the last compute.

**Recovery:** Use this shape and inspect the normalized object:

```python
section_dict = {
    "west_east": ((0.0, 0.0), (1000.0, 0.0), (80, 60)),
}
gp.set_section_grid(model.grid, section_dict)
print(model.grid.sections.names)
print(model.grid.sections.df)
gp.compute_model(model)
```

Endpoints are world X/Y pairs and must differ. The vertical range comes from
the base regular-grid Z extent. Call the viewer with the exact stored name;
`"topography"` is a special map-view token, not a replacement for a custom
section name.

## Random topography fails during generation

**Symptom:** A missing SciPy error, invalid resolution error, or a surface with
unexpected elevations.

**Likely causes:** SciPy is not installed; the topography resolution has a
component below 2; `d_z` is outside the model's intended Z range; or there is
no defined regular grid.

**Recovery:** Install the documented optional scientific dependency through the
environment route. Then check `model.grid.regular_grid`, use a two-component
resolution such as `[50, 50]`, and pass finite `d_z` values appropriate to the
model extent:

```python
topo = gp.set_topography_from_random(
    model.grid,
    fractal_dimension=1.2,
    d_z=[300.0, 750.0],
    topography_resolution=[50, 50],
)
assert topo.values_2d.shape == (50, 50, 3)
```

Seed NumPy before generation when a repeatable synthetic surface is needed.
Do not confuse `topography_resolution=[nx, ny]` with the 3-D model resolution.

## Array topography produces NaNs or missing-dependency errors

**Symptom:** `set_topography_from_arrays` raises a SciPy import error or the
surface contains NaNs.

**Likely causes:** The array setter uses SciPy `griddata`; the input vertices
do not cover the model's XY footprint; coordinates are not `(n, 3)`; or Z is
not finite.

**Recovery:** Install SciPy, validate the array, and provide enough XY coverage
for the regular-grid extent:

```python
vertices = np.asarray(vertices, dtype=float)
assert vertices.ndim == 2 and vertices.shape[1] == 3
assert np.isfinite(vertices).all()
topo = gp.set_topography_from_arrays(model.grid, vertices)
assert np.isfinite(topo.values).all()
```

If the data are already on a structured topography file, use the file setter
with the optional `subsurface` reader instead. Do not call the unimplemented
GDAL/array placeholder functions.

## File topography cannot be read

**Symptom:** `set_topography_from_file` reports that `subsurface` is missing or
the reader rejects the file.

**Cause:** The file path is delegated to `subsurface.modules.reader` and is not
a generic NumPy loader. The optional package or a supported structured raster
format is absent.

**Recovery:** Confirm the optional package and format in the environment route,
then pass a valid reader path and optional `crop_to_extent`. For a self-contained
fallback, convert the input externally to a finite XYZ vertex array and use
`set_topography_from_arrays`; for a test/demo, use the random setter. Do not
silently substitute a local checkout-relative example path.

## 2-D viewer is missing or opens an unwanted window

**Symptom:** `import gempy_viewer` fails, or a plot call attempts to use a GUI
in a headless process.

**Cause:** `gempy_viewer` is an optional package; 2-D plotting also uses
Matplotlib. The default `show=True` behavior is interactive when the backend is
not Agg.

**Recovery:** For a display-free check, set the Matplotlib backend before
importing pyplot and build with `show=False`:

```python
import matplotlib
matplotlib.use("Agg")
import gempy_viewer as gpv
p = gpv.plot_2d(model, direction="y", cell_number="mid", show=False)
p.fig.savefig("section.png", dpi=150)
```

If the viewer is not installed, validate grids and computed arrays without
plotting and report the optional omission. Do not make viewer installation a
prerequisite for grid selection.

**Symptom:** A topography-enabled 2-D view fails while ordinary sections work,
with an error naming `skimage` or `scikit-image`.

**Cause:** GemPy's topography masking and the viewer's topography drawer use
scikit-image in this version. It is an optional dependency even when the core
model imports successfully.

**Recovery:** Install the optional scientific/viewer dependencies through the
environment route, or temporarily plot the geological section with
`show_topography=False`. Keep the configured topography grid and do not replace
it with a fabricated overlay just to bypass the missing package.

## 3-D PyVista/VTK fails in headless execution

**Symptom:** `plot_3d` raises a PyVista/VTK/OpenGL/display-server error or hangs
while showing a scene.

**Cause:** 3-D rendering is optional and may need PyVista, VTK, an off-screen
backend, or host display support. A successful GemPy compute does not prove the
host can render.

**Recovery:** Separate model/grid validation from rendering. Try
`gpv.plot_3d(model, show=False, kwargs_plotter={"off_screen": True})` or
`image=True` only when off-screen support is installed. For a 2-D artifact use
the Agg workflow above. If the renderer remains unavailable, keep the model
result and record 3-D visualization as an environment limitation; do not alter
active flags or coordinates to hide a rendering failure.

## Plot is empty or shows stale results

**Symptom:** A section, topography map, or lithology panel is blank, or it does
not reflect the most recent grid configuration.

**Likely causes:** The model has not been computed after adding the grid; the
viewer was asked to show results when `model.solutions is None`; a section name
is wrong; or the active grid does not include the requested component.

**Recovery:** Check `model.solutions`, `active_grids`, component shapes, and
exact section names. Recompute after all setters, then choose a focused view:

```python
print(model.solutions is not None)
print(model.grid.active_grids)
print(getattr(model.grid.sections, "names", None))
gp.compute_model(model)
gpv.plot_2d(model, section_names=["west_east"], show=False)
```

Use `show_data=True` for an input-only diagnostic and disable result layers
when intentionally viewing an uncomputed model.
