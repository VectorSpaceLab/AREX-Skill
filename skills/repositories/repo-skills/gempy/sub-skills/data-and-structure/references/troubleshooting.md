# Data and structure troubleshooting

Use this page after the router in `SKILL.md` when construction, import, or
mutation fails. Keep a small inline fixture and report the exact exception,
selected rows, names, IDs, and table lengths.

## Import and schema failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ImportError` mentioning pandas | `.df` or a CSV reader was used without the optional pandas dependency | Install the package variant that supplies pandas, or work with `.data`, `.xyz`, and `from_arrays` instead; route installation issues to `environment-and-troubleshooting`. |
| `KeyError: 'X'`, `'formation'`, or a custom column | The file does not use the reader's canonical names or the override is wrong | Inspect headers, then pass `coord_x_name`, `coord_y_name`, `coord_z_name`, `surface_name`, and for gradient data `gx_name`/`gy_name`/`gz_name`. Use `pandas_kwargs={"sep": "\t"}` for tab-delimited input. |
| `KeyError` for a surface name while constructing a table | An explicit `name_id_map` lacks one of the names | Build the map from the complete shared name set and pass the same map to both tables. |
| Rows load but become different elements than expected | Name spelling/case differs (`Sand` vs `sand`) or the surface column was not selected | Normalize names before construction and inspect `table.name_id_map` and `frame.element_name_id_map`. |
| Orientation values are all zero or unexpected | Angle columns were interpreted with wrong units, polarity, or column aliases | `read_orientations` expects azimuth/dip in degrees and polarity as a multiplier. Inspect `ori.grads`; use explicit `G_x/G_y/G_z` when the source already has pole vectors. |

The reader mutates the DataFrame it standardizes internally, not the caller's
file. It does not repair missing values or infer a geological name from a row
number. Reject missing/non-numeric coordinates before model construction.

## Shape and numeric failures

`from_arrays` is row-oriented. Before calling it, check:

```python
arrays = [np.asarray(v) for v in (x, y, z, names)]
assert len({len(v) for v in arrays}) == 1
assert np.isfinite(np.asarray(x, dtype=float)).all()
assert np.isfinite(np.asarray(y, dtype=float)).all()
assert np.isfinite(np.asarray(z, dtype=float)).all()
```

For orientations, also require `np.asarray(pole_vector).shape == (n, 3)` or
`np.asarray(orientation).shape == (n, 3)`. A one-row vector should be shaped
`[[gx, gy, gz]]`, not `[gx, gy, gz]`. Do not pass a `(3, n)` matrix.

`ValueError: All input Sequences must have the same length` comes from the
`add_*` helpers. Count `x`, `y`, `z`, `elements_names`, pole/orientation rows,
and `nugget`; they must agree. `ValueError` about a nugget length means the
nugget array is not one value per row.

Structured-array assignment errors from `modify_*` usually mean that a NumPy
array has the wrong length for the selected rows or the wrong shape. Use a
scalar for broadcast or construct an array whose first dimension is exactly
`len(table.data[target_rows])`. Only use field names in the supported table
schema; names and IDs are identity fields and are not safe mutation targets.

## Names and structural hierarchy

`Element with name ... not found in the structural frame` means the target is
not already present. `gp.add_surface_points` and `gp.add_orientations` append
to existing elements; they do not create a new element. For a new surface:

1. construct its `SurfacePointsTable` and `OrientationsTable`;
2. construct `StructuralElement(name=..., color=..., ...)`;
3. append it to an existing group or add a new `StructuralGroup`;
4. verify `frame.elements_names` and `frame.element_name_id_map`;
5. only then add/mutate through the model API.

If a table's IDs do not match the frame, use the frame's aggregate copy and
assign it back rather than modifying only a detached table. Compare:

```python
set(model.surface_points_copy.ids) <= set(model.structural_frame.elements_ids)
set(model.orientations_copy.ids) <= set(model.structural_frame.elements_ids)
```

The frame includes a generated `basement` element in aggregate properties. Do
not add observations to it as if it were a normal input surface.

## Mutation selection and deletion

`modify_surface_points` rejects both `elements_names` and `slice`; choose one.
An element-name selection is by ID and may select several rows. A `slice` is
an aggregate global row selection, so inspect `model.surface_points_copy` first.
`modify_orientations` uses a global orientation slice.

The exported delete functions are currently stubs and raise
`NotImplementedError`. Do not retry them with guessed arguments. Filter an
aggregate copy by a stable numeric predicate or ID, assign it through
`model.surface_points = filtered` / `model.orientations = filtered`, and call
`model.validate()` immediately. Preserve the exact table dtype; rebuilding with
an ordinary 2-D array will fail the table constructor.

Angular keywords in `modify_orientations` are a current-version hazard. The
inspected implementation's angular branch raises an unpacking `ValueError`.
For a reliable edit, calculate or provide gradients and modify `G_x`, `G_y`,
and `G_z`. If a future package version changes this behavior, verify it with a
one-row test before updating a workflow claim.

## Plane-fit and orientation failures

`create_orientations_from_surface_points_coords` fits a plane using SVD. Give
it a finite `(n, 3)` array and at least three non-collinear points for each
fit. A subset is an array of index arrays, for example
`np.array([[0, 1, 2], [1, 2, 3]])`; every subset is fitted independently.

- `AssertionError` about points/dimensions: a subset has too few points or the
  array is transposed; use `(n_points, 3)`.
- NaN/Inf normal or unstable direction: source coordinates are non-finite or
  nearly collinear; clean or add points and inspect the returned `grads`.
- Normal points the opposite way: the fitter or source convention chose a
  different polarity. Flip the returned `grads` if the geological polarity is
  known, then validate the downstream model.

A fitted orientation is a table, not an element. Its `element_name` defaults
to `Generated`; use the actual target name when adding it or rebuild the table
with the intended name/ID map before attaching it.

## Model validation and structural relations

`model.validate()` raises `ModelValidationError` with `field`, `reason`,
`message`, and `context`. Repair based on `reason`:

- `empty_model`: add at least one surface-point or orientation row;
- `underdetermined_input`: add more than one surface point and/or an
  orientation; sparse data can still fail interpolation even after this gate;
- `empty_non_fault_group` / `empty_fault_group`: remove the empty group or add
  an element;
- `basement_relation_on_non_last_group`: move `BASEMENT` to the last group.

For `FAULT` groups, the frame's fault relation matrix must be square and match
the number of groups. Fault relations only point to younger groups. Use
`gp.set_is_fault(frame_or_model, names, faults_relation_type=...)` or
`gp.set_fault_relation(frame_or_model, matrix)` rather than hand-editing
individual matrix entries without checking shape. Mapping and final model
compute belong to [`modeling`](../../modeling/SKILL.md).
