# Core Data and Geometry Troubleshooting

## Scene path or file not found

**Symptom:** `Scene.at()` or `Scene.read()` raises `IOError` because the scene
path does not exist.

**Likely cause:** the scene directory was never created, was removed, or the
path was typed incorrectly.

**Recovery:**

1. Create a new scene with `Scene.create(parent_directory)`.
2. Confirm the path with `scene.path`.
3. Re-run the round-trip smoke helper if needed.

## Field / geometry mismatches

**Symptom:** `resample()`, `sample()`, or `Field.at()` complains about shape or
sampling incompatibility.

**Likely cause:** the source and target representations do not share the same
vector space, rank, or sample layout.

**Recovery:**

- Use `CenteredGrid` for scalar fields and `StaggeredGrid` for velocity-style
  vector fields.
- Sample to a compatible `Geometry` first, then convert back with `Field.at()`
  or `field.resample()`.
- Make sure geometry vector dimensions match the field's physical dimensions.

## Box constructor confusion

**Symptom:** `Box[0:1, 0:1]` or a bare `Box(...)` call raises an assertion
error.

**Likely cause:** the legacy constructor syntax was used or the dimension order
is missing.

**Recovery:** use `Box['x,y', 0:1, 0:1]` or the keyword form `Box(x=1, y=1)`.

## Legacy `Domain` warnings

**Symptom:** `phi.physics._boundaries.Domain` emits deprecation warnings.

**Likely cause:** old compatibility helpers are being used.

**Recovery:** construct grids directly with dictionaries and explicit
`extrapolation=` / `boundary=` values.

## Mesh or implicit-geometry issues

**Symptom:** mesh construction or mesh tests fail because SciPy symbols are
missing.

**Likely cause:** the environment lacks the mesh stack used by the unstructured
geometry helpers.

**Recovery:** install the missing scientific dependency set and rerun the smoke
helper or the mesh-specific native tests.

## Legacy file formats

**Symptom:** `field.read()` loads an old `.npz` file but the result looks odd.

**Likely cause:** the file came from an older PhiFlow version with legacy grid
layout conventions.

**Recovery:** compare the file against the legacy tests, then resave with the
current `Scene` / `field.write()` APIs.
