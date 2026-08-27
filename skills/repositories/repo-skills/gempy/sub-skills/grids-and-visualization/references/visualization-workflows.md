# Visualization workflows

Read this after the model has been configured and, for result views, after
`gp.compute_model(model)` has succeeded. Visualization is supplied by the
optional `gempy_viewer` package. The installed public signatures inspected for
this skill are:

```python
gpv.plot_2d(model, n_axis=None, section_names=None, cell_number=None,
            position=None, direction='y', series_n=0, legend=True, ve=1,
            block=None, override_regular_grid=None,
            kwargs_topography=None, kwargs_lithology=None,
            kwargs_scalar_field=None, kwargs_boundaries=None, **kwargs)

gpv.plot_3d(model, plotter_type='basic', active_scalar_field=None, ve=None,
            topography_scalar_type=..., kwargs_pyvista_bounds=None,
            kwargs_pyvista_camera=None, kwargs_plot_structured_grid=None,
            kwargs_plot_topography=None, kwargs_plot_data=None,
            kwargs_plotter=None, kwargs_plot_surfaces=None, image=False,
            show=True, transformed_data=False, show_nugget_effect=False,
            **kwargs)

gpv.plot_section_traces(model, section_names=None)
```

## 2-D orthogonal cuts

Use `direction` in `"x"`, `"y"`, or `"z"` to select an axis-aligned cut.
`cell_number` selects a grid index and accepts an integer or `"mid"`; it can
be a list when multiple panels are requested. `position` instead specifies a
world coordinate along the selected direction and is mutually exclusive with
`cell_number`:

```python
import gempy_viewer as gpv

p = gpv.plot_2d(
    model,
    direction=["y"],
    position=[1000.0],
    show_lith=True,
    show_boundaries=False,
    show_topography=True,
    show=False,
)
# p is Plot2D; p.axes[0] is a Matplotlib axis.
```

If no section or cell is supplied and `direction` is left at its default, the
viewer chooses the middle orthogonal cut. Prefer `position` when the model
resolution may change: it is expressed in model units, whereas a cell number
is a raw grid index. `show_lith`, `show_scalar`, `show_boundaries`,
`show_data`, `show_topography`, `show_section_traces`, and `show_results` are
passed as keyword arguments. Set `show_lith=False, show_boundaries=True` for
contact lines, or `show_scalar=True, show_lith=False, series_n=...` for one
structural series' scalar field. `series_n` is zero-based and can be a list for
multiple panels.

`ve` is vertical exaggeration. Keep it at `1` for geometry-faithful inspection;
use a larger value only for display. When adding custom Matplotlib overlays,
pass `show=False`, use the returned `.axes`, then save or display the figure in
the caller.

## Named sections and geological map

Configure named sections with `gp.set_section_grid` before computation. Then
select them by name:

```python
# The name must exactly match model.grid.sections.names.
p = gpv.plot_2d(
    model,
    section_names=["section_SW_NE"],
    show_lith=True,
    show_boundaries=False,
    show=False,
)
```

The special section name `"topography"` requests a top-down geological map
when a topography grid exists and has been computed:

```python
gpv.plot_2d(
    model,
    section_names=["topography"],
    show_topography=True,
    show_boundaries=False,
    show_data=True,
    show=False,
)
```

For a quick XY check of section traces, `gpv.plot_section_traces(model,
section_names=[...])` is available. It creates and shows a plot internally in
the inspected viewer version, so prefer `plot_2d(..., direction="z",
cell_number=-1, show=False, ...)` or a normal 2-D plot when strict headless
operation is required.

Multiple section names and orthogonal cuts can be combined in one call. Use
lists with matching panel semantics and verify the returned `p.axes` count
before applying per-panel overlays. A section's horizontal plot coordinate is
distance along its start-to-stop line, not necessarily world X or Y; project a
world XY point onto that line before overlaying a borehole on a named section.

## Topography display checks

`show_topography=True` on a 2-D orthogonal cut masks the part above the
surface; it does not create topography. Configure the surface with one of the
GemPy topography setters, compute it, and only then request a topography view.
For a named geological map, pass `section_names=["topography"]`. For 3-D, the
viewer defaults to showing topography when the grid contains one, but it can be
explicitly controlled with `show_topography=False` or `True`.

## 3-D inspection

`gpv.plot_3d` returns a `GemPyToVista` object. The result is a PyVista-backed
interactive scene. Common focused views are:

```python
# Result and input view; interactive when show=True.
gpv.plot_3d(model, show_data=True, show_lith=True,
            show_boundaries=True, show_topography=True)

# Input data only.
gpv.plot_3d(model, show_lith=False, show_boundaries=False,
            show_data=True, show_topography=False)

# Boundary surfaces only.
gpv.plot_3d(model, show_lith=False, show_boundaries=True,
            show_data=False, show_topography=False)

# A scalar field from a named generated field such as "sf_2".
gpv.plot_3d(model, active_scalar_field="sf_2", show_scalar=True,
            show_lith=False, show_topography=False)
```

The exact scalar field name is model-dependent; inspect the structural series
order and use the viewer's `sf_<zero-based-index>` convention exposed by the
current public examples. Do not guess a field index when the model has changed.
`ve` applies vertical scaling. `transformed_data=True` requests the model's
transformed coordinates instead of raw world coordinates and should only be
used when that distinction is intentional.

For custom geometry, construct without displaying and use the returned
PyVista plotter:

```python
p = gpv.plot_3d(model, show=False)
# p.p is the underlying PyVista plotter in the inspected public viewer object.
# Add caller-owned PyVista meshes here, then call p.p.show() when a display exists.
```

This pattern is optional and requires PyVista. Do not put display code in a
headless smoke test.

## Headless and saved-image modes

First check imports without opening a viewer:

```bash
python - <<'PY'
try:
    import gempy_viewer
    print("gempy_viewer available")
except ImportError as exc:
    print("viewer unavailable:", exc)
try:
    import pyvista
    print("pyvista available")
except ImportError as exc:
    print("3-D backend unavailable:", exc)
PY
```

For 2-D generation in a headless process, select a non-interactive Matplotlib
backend before importing `pyplot`, call `plot_2d(..., show=False)`, and save
with the returned figure:

```python
import matplotlib
matplotlib.use("Agg")
import gempy_viewer as gpv
p = gpv.plot_2d(model, direction="y", cell_number="mid", show=False)
p.fig.savefig("section.png", dpi=150, bbox_inches="tight")
```

For 3-D, `image=True` makes the viewer use an off-screen PyVista plotter and
renders through the viewer's image path; alternatively pass
`kwargs_plotter={"off_screen": True}` and `show=False` when constructing a
scene. A display server or VTK off-screen support may still be required by the
host. If construction fails with a VTK/PyVista display or OpenGL error, keep
the grid/model validation separate from visualization, use the 2-D Agg route,
and report 3-D as unavailable rather than changing model coordinates or
active-grid state. `fig_path="..."` is accepted as a 3-D keyword for the
viewer to request a screenshot; verify the file exists after the call.

The `image=True` route is not a substitute for `show=False` in a pure API
smoke test: it still creates a rendering pipeline. Use the viewer only when
its optional packages and host rendering capability are part of the requested
workflow.
