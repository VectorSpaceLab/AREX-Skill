# GemPy data-and-structure API reference

These are the public signatures and mutation semantics verified for the current
GemPy 3.x package line. Use `import gempy as gp` unless an import path is shown.
For exact behavior in another installed version, run `inspect.signature` and a
tiny fixture before relying on a changed keyword.

## Table classes

```python
from gempy.core.data import SurfacePointsTable, OrientationsTable

SurfacePointsTable(data=np.ndarray, name_id_map=None,
                   _model_transform=None)
SurfacePointsTable.from_arrays(x, y, z, names, nugget=None,
                               name_id_map=None)
SurfacePointsTable.initialize_empty()

OrientationsTable(data=np.ndarray, name_id_map=None,
                  _model_transform=None)
OrientationsTable.from_arrays(x, y, z, G_x, G_y, G_z, names,
                              nugget=None, name_id_map=None)
OrientationsTable.initialize_empty()
```

The direct `data=` constructor requires an array with the class's exact
structured dtype. Prefer `from_arrays` or `initialize_empty`. Public selectors:

```python
sp.get_surface_points_by_name(name)
sp.get_surface_points_by_id(id)
sp.get_surface_points_by_id_groups()
ori.get_orientations_by_name(name)
ori.get_orientations_by_id(id)
ori.get_orientations_by_id_groups()
```

`OrientationsTable.empty_orientation(id)` creates an empty orientation table
with that ID, useful when a surface element is known but has no orientation yet.
`fill_missing_orientations_groups` is an internal-style class utility for group
alignment; use `StructuralFrame.from_data_tables` for normal construction.

## Structural classes

```python
from gempy.core.data import (
    StructuralElement, StructuralGroup, StructuralFrame,
    StackRelationType, FaultsRelationSpecialCase,
)

StructuralElement(name, surface_points, orientations, id=-1,
                  is_active=True, color=None)
StructuralGroup(name, elements, structural_relation,
                fault_relations=None, faults_input_data=None,
                custom_interpolation=None, ignored_grid_types=())
StructuralFrame(structural_groups, color_gen)
StructuralFrame.from_data_tables(surface_points, orientations)
StructuralFrame.initialize_default_structure()
```

The engine enum is available as `gp.data.StackRelationType`. Fault relation
special cases are `OFFSET_FORMATIONS`, `OFFSET_NONE`, and `OFFSET_ALL`.
`StructuralGroup.is_fault` and `.is_lithology` derive from
`structural_relation`. `StructuralFrame.fault_relations` is a square boolean
matrix, one row/column per group. The frame computes it from each fault group's
`fault_relations`; a fault may affect all younger groups, none, formations only,
or an explicit list of younger groups. An explicit relation to an older group
raises `ValueError`.

Frame editing and lookup:

```python
frame.get_element_by_name(name)       # ValueError if absent
frame.get_group_by_name(name)         # ValueError if absent
frame.get_group_by_element(element)   # ValueError if absent
frame.append_group(group)
frame.insert_group(index, group)
group.append_element(element)
group.remove_element(element)
```

Manipulation helpers for a `GeoModel`:

```python
gp.add_structural_group(
    model, group_index, structural_group_name, elements,
    structural_relation,
    fault_relations=gp.data.FaultsRelationSpecialCase.OFFSET_ALL,
    custom_interpolation=None,
)
gp.remove_structural_group_by_index(model, group_index)
gp.remove_structural_group_by_name(model, group_name)
gp.remove_element_by_name(model, element_name)
```

The helpers return `StructuralFrame`. They do not automatically invent missing
surface tables, map names, or ensure a compute-ready input set.

## Input manipulation

```python
gp.add_surface_points(model, x, y, z, elements_names, nugget=None)
gp.add_orientations(model, x, y, z, elements_names,
                    pole_vector=None, orientation=None,
                    nugget=None, name_id_map=None)
gp.modify_surface_points(model, slice=None, elements_names=None, **fields)
gp.modify_orientations(model, slice=None, **fields)
gp.delete_surface_points()  # currently raises NotImplementedError
gp.delete_orientations()    # currently raises NotImplementedError
```

`add_surface_points` and `add_orientations` find every target by exact element
name, append into that element's table, and return the frame. They validate
sequence lengths with `ValueError`. `add_orientations` requires one of
`pole_vector` or `orientation`; angular `orientation` rows are
`[azimuth, dip, polarity]` and are converted immediately to stored gradients.

`modify_surface_points` fields are structured names `X`, `Y`, `Z`, and
`nugget`. `elements_names` selects all rows with those element IDs; alternatively
`slice` selects aggregate row positions. Both selectors together are rejected.
`modify_orientations` has the same aggregate `slice` behavior and accepts
`X/Y/Z`, `G_x/G_y/G_z`, and `nugget`. A NumPy array field must match the selected
row count. A scalar can be assigned to a selected structured field.

Although angular field names appear in the function docstring, the inspected
implementation's angular branch currently unpacks the `(n, 3)` result of its
converter incorrectly and raises `ValueError`. Use direct gradient fields for
reliable current-version edits. This note is intentional: do not silently
replace it with an unverified angular workaround.

## Derived orientations

```python
gp.create_orientations_from_surface_points_coords(
    xyz_coords, subset=None, element_name="Generated"
)
```

`xyz_coords` is an `(n, 3)` numeric array. Without `subset`, the function fits
one plane and returns one `OrientationsTable` row. With `subset`, pass index
arrays such as `np.array([[0, 1, 2], [1, 2, 3]])` to fit one plane per subset.
Each subset needs enough non-degenerate points for a meaningful fit.

## Reader functions

```python
from gempy.API.io_API import read_surface_points, read_orientations

read_surface_points(path, coord_x_name="X", coord_y_name="Y",
                    coord_z_name="Z", surface_name="formation",
                    name_id_map=None, pandas_kwargs=None)
read_orientations(path, coord_x_name="X", coord_y_name="Y",
                  coord_z_name="Z", gx_name="G_x", gy_name="G_y",
                  gz_name="G_z", surface_name="formation",
                  name_id_map=None, pandas_kwargs=None)
```

Both default to comma-separated pandas input. Pass `pandas_kwargs` such as
`{"sep": "\t"}`. For an orientation file using `azimuth`, `dip`, and
`polarity`, the reader derives the gradient components before constructing the
table. Pass the surface table's map into the orientation reader when files
share element names.

## Validation and diagnostic properties

```python
model.validate()
frame.element_name_id_map
frame.element_id_name_map
frame.surface_points_copy
frame.orientations_copy
```

`model.validate()` returns `None` on success and raises
`gempy.data.ModelValidationError` on the first semantic failure. Inspect
`exc.field`, `exc.reason`, `exc.message`, and `exc.context`. Data-table shape
errors and missing names generally raise ordinary `ValueError`, `TypeError`,
or a NumPy assignment error before semantic validation. After a successful
validation, route model creation/compute to [`modeling`](../../modeling/SKILL.md).
