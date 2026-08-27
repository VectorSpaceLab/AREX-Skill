# Modeling troubleshooting and recovery

Use this page after recording the model shape, group mapping, point/orientation
counts, grid choice, backend, and exact exception. Repair one layer at a time:
construction → data → mapping → relations → validation → backend/engine.

## 1. Construction and data triage

### `create_geomodel` rejects the inputs

- `ValueError: Either structural_frame or importer_helper must be provided`:
  pass `structural_frame=gp.data.StructuralFrame.initialize_default_structure()`
  for a synthetic model, or pass a configured `gp.data.ImporterHelper`. The
  constructor does not invent a data frame.
- `TypeError` or grid errors: verify that `extent` has six numeric values in
  min/max x, y, min/max z order and that `resolution` has three positive integer
  values. Use a tiny dense grid while diagnosing.
- A file-based importer failure is an input/environment problem. Confirm paths,
  column names, and optional tabular dependencies in the data sub-skill. Do not
  replace a failed local path with an unverified network URL.
- If the package accepts `resolution`, it initializes a dense grid; if it is
  omitted, it initializes an octree. Do not assume that `refinement` controls a
  dense-grid resolution.

### No element matches a point name

`gp.add_surface_points` and `gp.add_orientations` look up each
`elements_names` value in the structural frame and raise when the name is
unknown. Inspect:

```python
for group in model.structural_frame.structural_groups:
    print(group.name, [element.name for element in group.elements])
```

Add or rename the structural element through the data sub-skill before adding
rows. Mapping group names (`"Strat_Series"`) does not rename element names
(`"rock1"`), so do not use a group name in `elements_names` unless an element
has that exact name.

### Data is empty or too sparse

Run the semantic gate before compute:

```python
try:
    model.validate()
except gp.ModelValidationError as exc:
    print({"reason": exc.reason, "field": exc.field, "context": exc.context})
```

The precedence is deterministic:

1. `empty_model`: both all surface-point rows and all orientation rows are zero.
2. `empty_fault_group` or `empty_non_fault_group`: a group has no elements.
3. `underdetermined_input`: at most one surface point and no orientations.
4. `basement_relation_on_non_last_group`: a `BASEMENT` group is not last.

Add real, non-duplicate point rows and at least one valid orientation for a
small synthetic model. An orientation can be supplied as a pole vector with
shape `(n, 3)` or as `(azimuth, dip, polarity)` triples through the data API.
Validation only counts rows; it does not guarantee a well-conditioned
interpolation system. If the semantic gate passes but the engine reports a
singular/ill-conditioned system, inspect duplicate locations, coincident
surfaces, zero-length/invalid pole vectors, and the structural ordering.

`ModelValidationError` is a structured `ValueError`; preserve `reason`, `field`,
and `context` in a caller-facing diagnostic. The exception's string is concise
and should not be used as a substitute for those attributes.

## 2. Mapping and relation failures

### Mapping silently leaves a surface behind

`map_stack_to_surfaces` prints `Could not find element '<name>' in any group`
for a missing element rather than failing immediately. Always inspect:

```python
print(model.structural_frame.groups_to_mapper)
```

Every intended element must occur exactly once. If an old empty group remains,
use `remove_unused_series=True` (the default) or repair the frame explicitly.
Mapping mutates the structural frame, so recompute the final group count after
mapping before preparing a fault matrix.

### Bad mapping creates empty groups

A destination group is created when `set_series=True`, even if an element name
is misspelled. If it has no elements, `model.validate()` raises
`empty_non_fault_group` (or `empty_fault_group` if it was marked as a fault).
Fix the element spelling, map the real element, or remove the unused group. Do
not use `skip_validation=True` to hide an empty structural group.

### Fault group is not recognized

`set_is_fault(model, ["Fault_Series"])` searches group names, not element names.
The correct order is:

```python
gp.map_stack_to_surfaces(
    model,
    {"Fault_Series": "fault1", "Strat_Series": ("rock2", "rock1")},
)
gp.set_is_fault(model, ["Fault_Series"])
```

Then inspect:

```python
for group in model.structural_frame.structural_groups:
    print(group.name, group.structural_relation, group.is_fault, group.elements)
print(model.structural_frame.fault_relations)
```

A missing group name raises `ValueError`. A fault group with no elements fails
validation before computation.

### Fault relation matrix has wrong shape or direction

`set_fault_relation` requires a square boolean-like matrix whose dimensions are
the final number of structural groups. Build it only after mapping:

```python
n = len(model.structural_frame.structural_groups)
relation = np.zeros((n, n), dtype=bool)
relation[0, 1] = True       # group 0 affects younger group 1
# relation[1, 0] = True would describe an invalid backward relation
gp.set_fault_relation(model, relation)
```

The structural frame setter uses each row to derive special cases or an
explicit affected-group list. A matrix with the wrong shape triggers an
assertion. A fault affecting an older fault can raise `ValueError` when the
fault-relation property is evaluated. Keep diagonal entries false and set only
intended younger columns. The default from `set_is_fault` is often sufficient;
use a matrix only when the default `OFFSET_FORMATIONS`, `OFFSET_ALL`, or
`OFFSET_NONE` does not express the geology.

### Unconformity or structural relation behaves unexpectedly

A mapping with multiple groups is required to express separate structural
sequences, for example:

```python
gp.map_stack_to_surfaces(
    model,
    {"Strat_Series1": "rock3", "Strat_Series2": ("rock2", "rock1")},
)
```

This establishes groups but does not add missing data or automatically prove an
unconformity. Confirm that the final order is oldest-to-youngest as expected by
the model and that the last group is treated as the basement by the structural
frame's descriptor. A `BASEMENT` relation assigned to a non-final group is a
hard validation error.

## 3. Validation, skip, and compute errors

### `compute_model` fails before engine initialization

By default, `compute_model` calls `model.validate()` first. Treat a
`ModelValidationError` as a model-repair task, not as a backend failure. Fix
`exc.reason` and rerun validation explicitly. `skip_validation=True` is only for
controlled experiments where an external validator has already checked the
model; it can expose obscure downstream errors and must not be the normal fix.

Example diagnostic wrapper:

```python
config = gp.data.GemPyEngineConfig(
    backend=gp.data.AvailableBackends.numpy,
    use_gpu=False,
)
try:
    model.validate()
    solution = gp.compute_model(model, engine_config=config)
except gp.ModelValidationError as exc:
    raise RuntimeError(
        f"repair {exc.reason} at {exc.field}: {exc.context}"
    ) from exc
```

### Backend or engine initialization fails

Start with `AvailableBackends.numpy` and `use_gpu=False`. Record the selected
backend, `dtype`, `compute_grads`, and GPU flag. If NumPy succeeds but PyTorch
fails, the model is not necessarily wrong; check the installed matching
`gempy_engine`/PyTorch versions and route dependency work to
environment-and-troubleshooting. If GPU initialization fails, remove the GPU
request. The implementation supports an explicit `GEMPY_GPU_FALLBACK=True`
environment setting that changes a failed GPU request to CPU, but report the
fallback rather than claiming a GPU run.

An unsupported backend raises `ValueError`. Do not pass legacy backend enums to
this v3 compute path unless the installed API explicitly supports them.

### Numerical or tensor errors after validation

Reduce the problem in this order:

1. use the smallest dense `[8, 8, 8]` grid and CPU NumPy;
2. retain one structural group and one surface with several distinct points;
3. add one orientation with a finite, nonzero pole vector;
4. call `model.update_transform()` only if points were changed substantially;
5. add additional surfaces/groups and relations one at a time;
6. increase resolution/refinement only after the tiny case computes.

Do not use plotting or mesh extraction as a compute diagnostic. A successful
`model.validate()` is necessary but not sufficient for numerical conditioning.

### `compute_model_at` has surprising side effects

`compute_model_at` calls `set_custom_grid(..., reset=True)` and computes the model.
It prints a warning and leaves the custom grid active. Save the coordinates,
check that `at` is a numeric `(n, 3)` array inside the model extent, and inspect
the returned `raw_arrays.custom`. If a later full-grid result is unexpectedly
small or has the wrong active grid, route grid reset/reconfiguration to
`grids-and-visualization`; do not assume `compute_model_at` is read-only.

## 4. Optional dependencies and safe boundaries

Core construction and the CPU/NumPy compute path require the installed GemPy
package and its matching `gempy_engine`. Viewer, PyTorch, GPU, PyKeOps,
Subsurface, pandas-based import, and other plugin paths are additive. A missing
optional package should be reported with the requested workflow and its
prerequisite; do not silently switch a requested plugin workflow to a different
scientific result.

Built-in and source-documented examples may use external data or plotting. For
recovery and tests, prefer the tiny in-memory recipe in the modeling skill. Do
not tell a user to run a checkout-relative example file, and do not make a
network fetch part of the minimal modeling proof.
