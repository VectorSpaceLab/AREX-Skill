# Mesh troubleshooting

## Non-simplicial input

- Symptom: a mesh or geometry import fails because the input has polygons/polyhedra that do not fit the simplicial model.
- Likely cause: the source data was not triangulated/tetrahedralized first.
- Fix: convert the data to a simplicial mesh before building a `Mesh`.

## Wrong field ranks or shapes

- Symptom: point/cell data attachment fails or produces confusing downstream errors.
- Likely cause: the leading dimension does not match the point or cell count.
- Fix: check tensor ranks and the number of points/cells before attaching data.

## Validation failures

- Symptom: `validate_mesh` reports degenerate, duplicate, inverted, or out-of-bounds issues.
- Likely cause: topology or indexing problems in the source mesh.
- Fix: repair or clean the mesh, then validate again before expensive operations.

## Optional visualization dependencies

- Symptom: PyVista/VTK conversion or notebook visualization fails.
- Likely cause: the optional visualization stack is not installed.
- Fix: install the mesh visualization extra only if the workflow needs it.

## CPU/CUDA confusion

- Symptom: the mesh looks correct on CPU but a CUDA path fails or vice versa.
- Likely cause: the workflow did not move the whole mesh and its attached data together.
- Fix: verify the target device and re-run the tiny smoke before a larger workflow.
