---
name: data-and-structure
description: "Construct, inspect, import, and mutate GemPy input tables and
  structural frames; use this for surface points, orientations, elements,
  groups, IDs, colors, and input validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: EUPL 1.2
---

# GemPy data and structure

Use this sub-skill when a request concerns **input data or geological
organization**, before model interpolation. A GemPy model stores input in this
hierarchy:

`GeoModel -> StructuralFrame -> StructuralGroup -> StructuralElement -> SurfacePointsTable + OrientationsTable`.

A group is an ordered series/stack (or a fault group); an element is one named
surface or fault. The frame's group order is geological structure, not merely a
container order. Keep the same element names/IDs in surface points and
orientations, and validate before computing.

## Route and boundaries

- Construct or compute a model, map a stack to surfaces, or run interpolation:
  use [`modeling`](../modeling/SKILL.md).
- Configure regular/custom/section/topography grids or plot input/results: use
  [`grids-and-visualization`](../grids-and-visualization/SKILL.md).
- Save/load JSON or `.gempy`, or use advanced mesh/plugin workflows: use
  `serialization-and-advanced`.
- Install GemPy or diagnose missing pandas/viewer/engine dependencies: use
  `environment-and-troubleshooting`.

The public data API is available through `gempy as gp` and `gp.data`. The
recipes below use only caller-provided arrays, DataFrames, or file paths; they
do not require GemPy's source checkout or example data.

## Core workflow

1. Build `SurfacePointsTable` and `OrientationsTable` from equal-length numeric
   arrays, usually with `from_arrays`.
2. Use one explicit `name_id_map` for both tables when IDs must be controlled;
   otherwise let GemPy generate an opaque ID per distinct name.
3. Build a frame with `StructuralFrame.from_data_tables(surface_points,
   orientations)` or start with `StructuralFrame.initialize_default_structure()`
   for incremental `GeoModel` construction.
4. Inspect `frame.elements_names`, `element_id_name_map`, counts, and the table
   `.df`/`.data` before mapping or computing.
5. Mutate through `gp.add_*`/`gp.modify_*`, or replace a frame table through the
   model setter. Re-run `model.validate()` and then route computation to
   [`modeling`](../modeling/SKILL.md).

A minimal direct construction is:

```python
import numpy as np
import gempy as gp

sp = gp.data.SurfacePointsTable.from_arrays(
    x=np.array([0., 1., 0.]), y=np.array([0., 0., 1.]), z=np.array([0., 0., 0.]),
    names="Layer",
)
ori = gp.data.OrientationsTable.from_arrays(
    x=np.array([0.5]), y=np.array([0.5]), z=np.array([0.]),
    G_x=np.array([0.]), G_y=np.array([0.]), G_z=np.array([1.]),
    names=["Layer"], name_id_map=sp.name_id_map,
)
frame = gp.data.StructuralFrame.from_data_tables(sp, ori)
```

`from_data_tables` creates one default erosional group and an element for each
surface-point ID. An element with no matching orientation receives an empty
orientation table; this is allowed as a data structure, but may be insufficient
for later model validation/computation.

## Input/mutation recipes

### Add to an existing model

```python
# model must already contain an element named "Layer"
gp.add_surface_points(
    model, x=[2., 3.], y=[0., 0.], z=[1., 1.],
    elements_names=["Layer", "Layer"],
)
gp.add_orientations(
    model, x=[2.], y=[0.], z=[1.], elements_names=["Layer"],
    pole_vector=np.array([[0., 0., 1.]]),
)
```

`add_surface_points` and `add_orientations` append rows to the named element
and return the model's `StructuralFrame`. All coordinate/name/pole/nugget
sequences must have the same length. An unknown element name raises
`ValueError`; neither `add_*` creates a new element. Create an element and put
it in a group first when adding a new surface.

`add_orientations` accepts a representation in one of these forms:

- `pole_vector`: an `(n, 3)` array of gradient components `[G_x, G_y, G_z]`.
- `orientation`: an `(n, 3)` array `[azimuth_degrees, dip_degrees, polarity]`.

Pass one representation. If both are supplied, the current implementation
converts `orientation` and ignores the supplied pole vector. A missing
representation raises `ValueError`. A missing nugget uses GemPy's
current defaults (`0.01` for orientations and `0.00002` for surface points).

### Modify existing rows

```python
# Target by element name, or use a global row index/slice.
gp.modify_surface_points(model, elements_names=["Layer"], Z=np.array([1., 1., 2.]))
gp.modify_surface_points(model, slice=0, X=0.25, nugget=0.00002)
gp.modify_orientations(
    model, slice=slice(0, 1),
    G_x=np.array([0.0]), G_y=np.array([0.0]), G_z=np.array([1.0]),
)
```

`modify_surface_points` accepts `X`, `Y`, `Z`, and `nugget`;
`modify_orientations` accepts those coordinates plus `G_x`, `G_y`, `G_z`, and
`nugget`. Scalars broadcast through NumPy structured-array assignment; arrays
must match the selected row count. Surface-point selection cannot specify both
`elements_names` and `slice`. These functions update the model through the
frame table setters; returned value is the updated `StructuralFrame`.

The current inspected GemPy release exposes angular keyword handling in
`modify_orientations`, but its implementation raises an unpacking `ValueError`
when `azimuth`, `dip`, or `polarity` is used. Treat angular modification as a
known compatibility gap: convert angles yourself and write `G_x/G_y/G_z`, or
recreate the orientation rows with `add_orientations`. Do not claim angular
modification works unless a later package version is verified.

### Delete rows or elements

`gp.delete_surface_points()` and `gp.delete_orientations()` are exported but
currently are zero-argument stubs that raise `NotImplementedError`; they do not
provide a selector. For a controlled row deletion, filter a copy and assign it
back, preserving the structured dtype:

```python
sp = model.surface_points_copy
keep = sp.data["Z"] >= 0.0
sp.data = sp.data[keep]
model.surface_points = sp

ori = model.orientations_copy
keep_ori = ori.data["X"] != 2.0
ori.data = ori.data[keep_ori]
model.orientations = ori
model.validate()
```

This is a low-level workaround: filter by the table's numeric fields or IDs,
never by an assumed row order, and validate immediately. Removing the only
observations can make the model empty or underdetermined.

## Validation gate

Before handing off to modeling, check `model.validate()`. It raises
`gempy.data.ModelValidationError`, whose useful attributes are `field`,
`reason`, `message`, and `context`. Current semantic checks include:

- no surface points **and** no orientations (`empty_model`);
- an empty structural group (`empty_non_fault_group` or `empty_fault_group`);
- at most one surface point with no orientation (`underdetermined_input`);
- a `BASEMENT` group before the final group (`basement_relation_on_non_last_group`).

For fault groups, accessing the frame's fault descriptor also requires a square
fault-relation matrix with one row/column per structural group. For a failure,
inspect `model.structural_frame.structural_groups`, `elements_names`, table
lengths, IDs, and `model.structural_frame.fault_relations`; repair the structure
before calling compute. A successful data-table construction is not proof that
interpolation is determined.

## Verification and recovery

Use the bundled table inspector for a caller-owned CSV pair:

```bash
python sub-skills/data-and-structure/scripts/inspect_tables.py \
  --surface-points points.csv --orientations orientations.csv
```

It reports canonical columns, row counts, IDs, names, and finite-value checks
without modifying files. For numeric/shape errors, first convert inputs with
`np.asarray(..., dtype=float)`, assert all row counts agree, and print
`table.data.dtype`/`table.data.shape`. For name/ID errors, pass the same
`name_id_map` to both constructors and compare it with
`frame.element_name_id_map`. For sparse inputs, add non-collinear surface
points and at least one orientation per interpolated element, then call
`model.validate()` again.

For more column-level contracts and structural relationships, read
[`references/data-formats.md`](references/data-formats.md) and
[`references/api-reference.md`](references/api-reference.md). For failures,
read [`references/troubleshooting.md`](references/troubleshooting.md). For
persistence, route the already validated model to
`serialization-and-advanced`; do not serialize ad hoc table internals as a
replacement for model persistence.
