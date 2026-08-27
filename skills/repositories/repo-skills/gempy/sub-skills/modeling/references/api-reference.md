# Modeling API reference

This reference records the public GemPy 3 API used by this sub-skill. Confirm the
installed GemPy and `gempy_engine` versions before relying on backend-specific
options; the spelling and defaults below follow the inspected package.

## Construction

### `gempy.create_geomodel`

```python
gp.create_geomodel(
    *,
    project_name: str = "default_project",
    extent: list | numpy.ndarray = None,
    resolution: list | numpy.ndarray = None,
    refinement: int = 1,
    structural_frame: gp.data.StructuralFrame = None,
    importer_helper: gp.data.ImporterHelper = None,
    intpolation_options_tye: InterpolationOptionsType = InterpolationOptionsType.OCTREE,
    **kwargs,
) -> gp.data.GeoModel
```

Important contract details:

- `extent` is `[min_x, max_x, min_y, max_y, min_z, max_z]`.
- With `resolution=[nx, ny, nz]`, initialization uses a dense regular grid.
  Without it, initialization uses an octree with `refinement` levels.
- Supply exactly one model-data source: a ready `structural_frame`, or an
  `importer_helper` whose point/orientation paths are readable. If both are
  `None`, construction raises `ValueError`.
- The keyword `intpolation_options_tye` is misspelled in the package signature;
  use that spelling only when overriding the default. Values are the enum
  `InterpolationOptionsType.DENSE_GRID` or `.OCTREE` from
  `gempy.core.data.options`.
- `legacy_octree_init=True` may be passed through `**kwargs` when compatibility
  with the legacy octree initializer is specifically required. It is not a
  general repair for invalid data.
- `structural_frame` is not copied by this API. Later mapping and relation calls
  mutate the model's frame.

A deterministic no-file constructor is:

```python
frame = gp.data.StructuralFrame.initialize_default_structure()
model = gp.create_geomodel(
    project_name="demo",
    extent=[0, 100, 0, 100, 0, 100],
    resolution=[8, 8, 8],
    structural_frame=frame,
)
```

`initialize_default_structure()` creates one ERODE group named
`default_formations` containing an empty element named `surface1`. It is a
container, not valid model data until points/orientations are added.

### `gempy.generate_example_model`

```python
from gempy.core.data.enumerators import ExampleModel

gp.generate_example_model(
    example_model: ExampleModel,
    compute_model: bool = True,
) -> gp.data.GeoModel
```

The source enum `ExampleModel` is imported from
`gempy.core.data.enumerators` and includes `TWO_AND_A_HALF_D`,
`HORIZONTAL_STRAT`, `ANTICLINE`, `ONE_FAULT`, `COMBINATION`,
`ONE_FAULT_GRAVITY`, `GRABEN`, `GREENSTONE`, and `FAULT_RELATION`. These
built-in generators are useful for API exploration, but
several source examples fetch external data or depend on optional packages.
Use `compute_model=False` when inspecting or modifying the returned model, and
then validate and compute it yourself. Do not treat an example generator as a
network-free smoke test unless the selected case has been checked in the
installed package.

## Structural mapping

### `gempy.map_stack_to_surfaces`

```python
gp.map_stack_to_surfaces(
    gempy_model: gp.data.GeoModel,
    mapping_object: dict[str, list[str] | tuple],
    set_series: bool = True,
    remove_unused_series: bool = True,
    series_data: list = None,
) -> gp.data.StructuralFrame
```

`mapping_object` maps the destination structural-group name to one or more
existing element names. A string is accepted and treated as one element. With
`set_series=True`, absent destination groups are created with the default
`StackRelationType.ERODE` unless matching `series_data` supplies a relation.
With `remove_unused_series=True`, groups left empty are removed.

The call moves elements in place. It prints a warning for an element name that
is not found rather than raising at that point, so inspect the result:

```python
gp.map_stack_to_surfaces(model, {"Strat_Series": ("surface1",)})
assert model.structural_frame.groups_to_mapper == {
    "Strat_Series": ["surface1"]
}
```

Map all elements before setting fault matrices. The matrix dimensions are the
number of structural groups *after* mapping and removal of unused groups.

## Computation

### `gempy.compute_model`

```python
gp.compute_model(
    gempy_model: gp.data.GeoModel,
    engine_config: gp.data.GemPyEngineConfig | None = None,
    skip_validation: bool = False,
    **kwargs,
) -> gp.data.Solutions
```

When `engine_config` is omitted, `GemPyEngineConfig()` supplies the package
configuration. For a deterministic CPU-first run:

```python
config = gp.data.GemPyEngineConfig(
    backend=gp.data.AvailableBackends.numpy,
    use_gpu=False,
)
solutions = gp.compute_model(model, engine_config=config)
```

The supported API branch accepts NumPy or PyTorch backends. Unsupported enum
values raise `ValueError`. `dtype` and `compute_grads` are optional fields on
`GemPyEngineConfig`; do not assume a dtype is accepted by every engine release.
If `use_gpu=True` cannot initialize, the API raises unless the environment
variable `GEMPY_GPU_FALLBACK=True` is set, in which case it changes the config
to CPU and prints a fallback message.

Before backend setup, `compute_model` calls `gempy_model.validate()` unless
`skip_validation=True`. On success it stores a `Solutions` object on
`model.solutions` and returns it. The solution setter also propagates scalar
fields and available meshes to structural elements. Use the returned object or
`model.solutions`; do not assume mesh arrays exist when mesh extraction is
turned off or not supported.

The optional keyword `validate_serialization=True` causes an additional internal
serialization round-trip; it belongs to diagnostic use and may activate the
serialization dependency path.

### `gempy.compute_model_at`

```python
gp.compute_model_at(
    gempy_model: gp.data.GeoModel,
    at: numpy.ndarray,
    engine_config: gp.data.GemPyEngineConfig | None = None,
    skip_validation: bool = False,
) -> numpy.ndarray
```

`at` is an array of coordinate rows, normally shape `(n, 3)`. The function
prints a warning, installs a custom grid on `model.grid` with `reset=True`,
computes the model using the same validation/backend path, and returns
`solutions.raw_arrays.custom`. This is a stateful operation: the custom grid
and active-grid selection remain on the model. Reconfigure the grid through the
grids sub-skill if a subsequent full-grid calculation is required.

## Faults and relations

### `gempy.set_is_fault`

```python
gp.set_is_fault(
    frame: gp.data.GeoModel | gp.data.StructuralFrame,
    fault_groups: list[str] | list[gp.data.StructuralGroup],
    faults_relation_type: gp.data.FaultsRelationSpecialCase =
        gp.data.FaultsRelationSpecialCase.OFFSET_FORMATIONS,
    change_color: bool = True,
) -> gp.data.StructuralFrame
```

Each named group must exist. The function sets its
`structural_relation=StackRelationType.FAULT` and its default fault relation,
optionally changing element colors. `OFFSET_FORMATIONS` affects younger
non-fault groups; `OFFSET_ALL` affects every younger group; `OFFSET_NONE`
affects none. A name that is not found raises `ValueError`.

`gp.unset_is_fault` is not exported by `gempy/API/__init__.py` in this version;
to undo a fault, set the relevant group relation to
`gp.data.StackRelationType.ERODE` and its fault relation to
`gp.data.FaultsRelationSpecialCase.OFFSET_NONE`, or use the owning data skill.
Do not call the source-private `_find_and_set_fields` helper.

### `gempy.set_fault_relation`

```python
gp.set_fault_relation(
    frame: gp.data.GeoModel | gp.data.StructuralFrame,
    rel_matrix: numpy.ndarray,
) -> gp.data.StructuralFrame
```

The matrix must be square with shape `(len(frame.structural_frame.structural_groups),) * 2`
(or the equivalent frame group count). The structural-frame setter converts
rows into `OFFSET_ALL`, `OFFSET_NONE`, or an explicit list of affected groups.
A row's `True` entries identify groups affected by that fault; relations to
older groups are invalid. Check the resulting matrix with
`model.structural_frame.fault_relations` and ensure every fault row is marked
with `StackRelationType.FAULT` before computing.

A small explicit setup is:

```python
# After mapping to Fault_Series, Strat_Series:
gp.set_is_fault(model, ["Fault_Series"])
gp.set_fault_relation(model, np.array([[False, True], [False, False]]))
```

If a fault group is first/older and a formation group is second/younger, the
matrix above expresses that the fault affects the formation. The exact number
and ordering of groups must be inspected rather than guessed.

## Validation contract

`model.validate()` raises `gp.ModelValidationError`, a `ValueError` subclass
with `.field`, `.reason`, `.message`, and `.context`. The first applicable rule
wins:

| Precedence | Reason | Condition | Field |
|---|---|---|---|
| 1 | `empty_model` | no surface points and no orientations | `input_data` |
| 2 | `empty_fault_group` | a fault group has no elements | `structural_groups[i]` |
| 3 | `empty_non_fault_group` | a non-fault group has no elements | `structural_groups[i]` |
| 4 | `underdetermined_input` | at most one surface point and no orientations | `input_data` |
| 5 | `basement_relation_on_non_last_group` | a BASEMENT group is not last | `structural_groups[i].structural_relation` |

Catch and expose the structured fields during repair:

```python
try:
    model.validate()
except gp.ModelValidationError as exc:
    print(exc.reason, exc.field, exc.context)
```

Validation does not prove that all interpolation constraints are numerically
well-conditioned. A model can pass these five semantic checks and still fail
in the engine due to duplicate points, degenerate orientations, bad relations,
or insufficient numerical data.
