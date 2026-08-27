# GemPy data formats and structural relationships

This reference is the detailed contract behind `data-and-structure/SKILL.md`.
All examples use caller-owned arrays or inline data; no repository fixtures are
required.

## Table schemas

GemPy's table objects wrap NumPy structured arrays. Construct them with the
public class methods rather than hand-writing a structured dtype unless a
low-level filter is necessary.

| Object | Required fields and dtypes | Meaning |
|---|---|---|
| `SurfacePointsTable` | `X`, `Y`, `Z`: `float64`; `id`: `int32`; `nugget`: `float64` | Coordinates marking a surface interface and its per-point nugget |
| `OrientationsTable` | `X`, `Y`, `Z`, `G_x`, `G_y`, `G_z`: `float64`; `id`: `int32`; `nugget`: `float64` | Orientation location, pole/gradient vector, and nugget |

Useful properties are `xyz` (an `(n, 3)` copy-like array), `xyz_view` (a
structured view with a setter), `ids`, `nugget`, and `df`. Orientations also
have `grads` and `grads_view`. The `.df` properties require pandas; `.data`
does not.

`SurfacePointsTable.from_arrays` has the public shape:

```python
SurfacePointsTable.from_arrays(
    x, y, z, names, nugget=None, name_id_map=None
)
```

`OrientationsTable.from_arrays` has the public shape:

```python
OrientationsTable.from_arrays(
    x, y, z, G_x, G_y, G_z, names, nugget=None, name_id_map=None
)
```

For each constructor, `x`, `y`, `z`, and every field array must have one value
per row. When `name_id_map` is omitted, `names` may be one string (broadcast to
all rows) or a sequence of exactly `n` names. When an explicit `name_id_map` is
passed, use a sequence of names—even for one row—because the current
implementation iterates a scalar string as characters in that branch. A
sequence with one name is **not** a broadcast request; use the string form only
without an explicit map, or repeat the name explicitly.

If `nugget` is omitted, the current defaults are `0.00002` for surface points
and `0.01` for orientations. Treat these as package defaults, not geological
measurements. Supply explicit values when reproducing a calibrated workflow.

## Names and IDs

Each table stores `name_id_map: dict[str, int]` in addition to the per-row
integer `id`. Without a map, GemPy generates one ID for each distinct name.
These IDs are identity keys, not row positions and not a promise of small
sequential integers. Do not use `ids == [0, 1, ...]` as a validity test.

When constructing separate tables, share the mapping:

```python
names = ["Sand", "Shale", "Sand"]
ids = {"Sand": 101, "Shale": 102}
sp = gp.data.SurfacePointsTable.from_arrays(
    [0., 1., 2.], [0., 0., 0.], [0., -1., -2.], names,
    name_id_map=ids,
)
ori = gp.data.OrientationsTable.from_arrays(
    [0.], [0.], [-1.], [0.], [0.], [1.], ["Sand"],
    name_id_map=ids,
)
```

If an explicit map omits a name, construction raises a key lookup error. If
surface points and orientations are built independently with different name
sets/orderings, their generated IDs can differ. Prefer passing the surface
point map into `read_orientations(..., name_id_map=surface_points.name_id_map)`
and compare `frame.element_name_id_map` after frame creation.

`SurfacePointsTable.get_surface_points_by_name/id` and
`OrientationsTable.get_orientations_by_name/id` return new table wrappers over
selected structured rows. The singular `.id` property is only valid when a
table contains exactly one unique ID; it raises `ValueError` for empty or
mixed-ID tables.

## Frame hierarchy

A direct element contains exactly one surface-point table and one orientation
table:

```python
element = gp.data.StructuralElement(
    name="Sand",
    surface_points=sp,
    orientations=ori,
    id=101,                 # optional; default is -1/name-derived behavior
    is_active=True,
    color="#015482",       # required valid hex string in practice
)
```

`StructuralElement` exposes `name`, `id`, `color`, `is_active`,
`number_of_points`, and `number_of_orientations`. Its color setter accepts a
3- or 6-digit hexadecimal string such as `#abc` or `#015482`; `None` is not a
valid runtime color even though the constructor annotation has a default.
Use `next(frame.color_generator)` for the default GemPy palette.

A group contains elements and a relation:

```python
group = gp.data.StructuralGroup(
    name="Stratigraphy",
    elements=[element],
    structural_relation=gp.data.StackRelationType.ERODE,
)
```

`StructuralGroup`, `Stack`, and `Fault` share the same constructor contract.
`Stack` and `Fault` are available types, but the relation enum is what controls
behavior. The current enum values are:

- `ERODE`: ordinary erosional/stratigraphic relation;
- `ONLAP`: onlap relation;
- `FAULT`: fault group;
- `BASEMENT`: basement relation, valid only for the final group during model
  semantic validation;
- `NULL_SPACE`: group excluded from some structural filtering.

A `StructuralFrame` is an ordered list of groups plus a color generator. Use
`StructuralFrame.initialize_default_structure()` for a valid starting shape or
`StructuralFrame.from_data_tables(sp, ori)` to derive elements/groups from
IDs. The direct constructor's live signature is
`StructuralFrame(structural_groups, color_gen)`; the parameter is named
`color_gen` even though the stored attribute is `color_generator`.

Inspect without relying on private fields:

```python
frame.elements_names
frame.elements_ids
frame.element_name_id_map
frame.element_id_name_map
frame.groups_to_mapper
frame.number_of_points_per_element
frame.number_of_points_per_group
frame.number_of_orientations_per_group
frame.group_is_fault
frame.group_is_lithology
frame.surface_points_copy
frame.orientations_copy
```

`surface_points_copy` and `orientations_copy` are aggregate copies intended for
inspection/editing. The frame's `surface_points` and `orientations` properties
are setters only: assigning a filtered/edited table redistributes rows by ID
back to each element. Do not expect `frame.surface_points` to return a table.

Use `append_group`, `insert_group`, `StructuralGroup.append_element`, and
`remove_element` for direct structural edits. The public manipulation helpers
also expose:

```python
gp.add_structural_group(model, group_index, structural_group_name,
                         elements, structural_relation,
                         fault_relations=...)
gp.remove_structural_group_by_index(model, group_index)
gp.remove_structural_group_by_name(model, group_name)
gp.remove_element_by_name(model, element_name)
```

`elements` must be a Python `list` of `StructuralElement` instances for
`add_structural_group`. Remove empty groups before model validation.

## Orientation representations

GemPy stores gradient components, not angular columns. When angles are used
for input, the public conversion is equivalent to:

```python
azimuth = np.deg2rad(azimuth_degrees)
dip = np.deg2rad(dip_degrees)
G_x = np.sin(dip) * np.sin(azimuth) * polarity
G_y = np.sin(dip) * np.cos(azimuth) * polarity
G_z = np.cos(dip) * polarity
```

Thus `orientation=[[90., 45., 1.]]` yields approximately
`[G_x, G_y, G_z] == [0.7071, 0.0, 0.7071]`. `pole_vector` is already the
three stored components and must be shaped `(n, 3)`.

`gp.create_orientations_from_surface_points_coords(xyz_coords,
subset=None, element_name="Generated")` fits a plane by SVD and returns one
orientation at the centroid when `subset` is absent. When `subset` is present,
it is an array-like collection of row-index arrays; one fitted orientation is
returned per subset. The implementation requires at least three points per
fit in 3-D (`assert`), and rank-deficient/collinear points do not provide a
reliable geological plane even if SVD returns a vector. Check finite values,
point count, and normal direction before adding the result to a model.

## Tabular file contract

`gempy.API.io_API.read_surface_points` and `read_orientations` use pandas and
accept a path plus optional column-name overrides and `pandas_kwargs`.
Defaults are comma-separated files with:

- surface points: `X`, `Y`, `Z`, `formation`;
- orientations: `X`, `Y`, `Z`, and either `G_x`, `G_y`, `G_z` or
  `azimuth`, `dip`, `polarity`, plus `formation`.

The reader standardizes public aliases: `x/y/z`, `Azimuth/Dip/Polarity`,
`Formation` or `surface`, and `gradient_x/gradient_y/gradient_z` are accepted.
`pandas_kwargs={"sep": ";"}` handles non-comma files. Column overrides are
safer than relying on aliases for unusual schemas.

```python
from gempy.API.io_API import read_surface_points, read_orientations

sp = read_surface_points("points.csv", surface_name="surface")
ori = read_orientations(
    "orientations.csv", surface_name="surface",
    name_id_map=sp.name_id_map,
)
frame = gp.data.StructuralFrame.from_data_tables(sp, ori)
```

If an orientation file has angular columns, the reader derives gradients. If it
has both angular and gradient columns, the angular triplet is used to derive
`G_x/G_y/G_z` in the current implementation. Reader paths are caller-owned;
there is no bundled data download requirement in this sub-skill.
