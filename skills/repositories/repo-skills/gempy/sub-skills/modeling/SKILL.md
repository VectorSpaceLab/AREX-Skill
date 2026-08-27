---
name: modeling
description: "Create and compute GemPy 3-D implicit geological models, organize
  structural relations, mark faults, and validate small synthetic workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: EUPL 1.2
---

# GemPy modeling

Use this skill when the request is to create a `GeoModel`, arrange surfaces into
structural groups, compute an implicit model, evaluate it at coordinates, or
model faults/unconformities. The public APIs are exported from `gempy` as `gp`.
Detailed signatures and relation semantics are in
[`references/api-reference.md`](references/api-reference.md); recovery guidance
is in [`references/troubleshooting.md`](references/troubleshooting.md).

## Route before acting

- Route surface-point/orientation table creation or mutation to
  [`data-and-structure`](../data-and-structure/SKILL.md).
- Route dense/custom/section/topography grids and plotting to
  [`grids-and-visualization`](../grids-and-visualization/SKILL.md).
- Route save/load, JSON, mesh, gravity, topology, and plugin integrations to
  [`serialization-and-advanced`](../serialization-and-advanced/SKILL.md).
- Route installation, import failures, and generic missing dependencies to
  [`environment-and-troubleshooting`](../environment-and-troubleshooting/SKILL.md).

For a modeling request, establish the extent, grid choice, surface names,
structural ordering, relations, backend, and whether the result is a full grid
or point evaluation. Do not silently fetch example data or run a plotting
viewer in a headless environment.

## Minimal modeling order

1. `import numpy as np` and `import gempy as gp`.
2. Build or load a `StructuralFrame`. For an empty synthetic model use
   `gp.data.StructuralFrame.initialize_default_structure()`; it supplies one
   empty element named `surface1` in `default_formations`.
3. Create the model with `gp.create_geomodel(...)`. Pass either
   `structural_frame=` or an `gp.data.ImporterHelper`; do not omit both.
4. Add or import points and orientations. Use the data sub-skill when data
   construction is the main task. Every `elements_names` value must identify an
   existing structural element.
5. Call `gp.map_stack_to_surfaces(...)` when the desired series/groups differ
   from the initial frame. Verify its result with
   `model.structural_frame.groups_to_mapper`.
6. Set structural relations, especially fault groups, **after** mapping. For
   faults use `gp.set_is_fault(model, ["Fault_Series"])`; set an explicit
   relation matrix only after the final group count is known.
7. Call `model.validate()` explicitly while developing, then
   `gp.compute_model(model, engine_config=...)`. Validation is enabled by
   default and runs before backend setup.
8. Inspect the returned `gp.data.Solutions` and the model's `solutions`; use
   `gp.compute_model_at(model, coordinates, engine_config=...)` for selected
   coordinates. `compute_model_at` changes the model's active custom grid.

## Choosing initialization

- Dense grid: `extent=[xmin, xmax, ymin, ymax, zmin, zmax]` and
  `resolution=[nx, ny, nz]`.
- Octree grid: omit `resolution` and use `refinement=<int>`.
- The exact keyword is currently misspelled in the public signature:
  `intpolation_options_tye=`. Its values are
  `InterpolationOptionsType.DENSE_GRID` or `.OCTREE` from
  `gempy.core.data.options` when explicitly selected. Prefer the default unless
  a caller needs a specific engine option.
- `resolution` takes precedence for grid initialization; `refinement` still
  controls the octree interpolation option. Keep a tiny resolution/refinement
  for diagnostics and scale only after the model computes successfully.

## Small synthetic workflow

```python
import numpy as np
import gempy as gp

frame = gp.data.StructuralFrame.initialize_default_structure()
model = gp.create_geomodel(
    project_name="flat_demo",
    extent=[0, 100, 0, 100, 0, 100],
    resolution=[8, 8, 8],
    structural_frame=frame,
)
gp.add_surface_points(
    model,
    x=[10, 90, 10, 90], y=[10, 10, 90, 90], z=[40, 40, 40, 40],
    elements_names="surface1",
)
gp.add_orientations(
    model, x=[50], y=[50], z=[40], elements_names=["surface1"],
    pole_vector=[[0.0, 0.0, 1.0]],
)
model.validate()
engine = gp.data.GemPyEngineConfig(
    backend=gp.data.AvailableBackends.numpy, use_gpu=False,
)
solutions = gp.compute_model(model, engine_config=engine)
values = gp.compute_model_at(
    model, np.array([[20.0, 20.0, 20.0], [80.0, 80.0, 80.0]]),
    engine_config=engine,
)
print(type(solutions).__name__, values.shape)
```

This is a self-contained recipe; it does not require example files or network
access. The bundled `scripts/tiny_model_smoke.py` runs the same public-API
pattern as a command-line check when the GemPy engine dependency is installed.

## Structural relations and compute gates

`map_stack_to_surfaces` moves named elements into named groups. Mapping is not
just cosmetic: the final group order drives stratigraphic and fault relations.
An unconformity pattern uses separate groups, for example
`{"Strat_Series1": "rock3", "Strat_Series2": ("rock2", "rock1")}`;
map first, then inspect and compute. A fault pattern maps a fault element into
its own group, maps formations into later groups, then marks that group with
`set_is_fault`.

`set_is_fault` accepts a `GeoModel` or `StructuralFrame` and fault group names
or `StructuralGroup` objects. Its default relation is
`FaultsRelationSpecialCase.OFFSET_FORMATIONS`. Use
`OFFSET_ALL` or `OFFSET_NONE` deliberately when that is the intended geology.
`set_fault_relation` accepts a square NumPy matrix in final structural-group
order; a `True` entry means the row fault affects the column group. Relations
must be forward/younger: a fault cannot affect an older fault group.

Call `model.validate()` before expensive computation. It reports the first
semantic violation as `ModelValidationError` with `.field`, `.reason`, and
`.context`. `gp.compute_model` calls the same validation by default. Only use
`skip_validation=True` for controlled diagnostics after you have independently
checked the model; it bypasses the safety gate and does not repair bad data.

## Backend and recovery rules

The supported compute path in this scope is NumPy or PyTorch through
`gp.data.GemPyEngineConfig`; a GPU is optional. Start with NumPy and
`use_gpu=False`. If a GPU is requested and unavailable, either remove the GPU
request or use the documented `GEMPY_GPU_FALLBACK=True` behavior; do not claim
that a successful CPU run proves CUDA support.

When compute fails, preserve the model and first record the validation reason,
group mapping, point/orientation counts, grid size, backend, dtype, and GPU
flag. Reduce to the minimal recipe above, then add one surface, relation, or
option at a time. Consult
[`references/troubleshooting.md`](references/troubleshooting.md) before
changing interpolation settings. Never solve a missing dependency by changing
structural data.
