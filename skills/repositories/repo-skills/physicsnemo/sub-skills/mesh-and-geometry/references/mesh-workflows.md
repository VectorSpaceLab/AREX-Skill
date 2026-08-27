# PhysicsNeMo mesh workflows

## Core flow

1. Create or load a `Mesh`.
2. Attach `point_data`, `cell_data`, or `global_data` with consistent leading dimensions.
3. Validate the mesh before expensive downstream work.
4. Use geometry/calculus/sampling/repair helpers only after the basic object shape is correct.
5. Move the mesh to the target device when the workflow is GPU-based.

## Typical tasks

### Create a mesh

- Build a `Mesh(points, cells)` for a simplicial mesh.
- Omit `cells` for a point cloud when the workflow is only point-based.

### DomainMesh workflows

- Use `DomainMesh(interior, boundaries=...)` when the problem has an interior mesh plus named boundary meshes.
- Validate boundary consistency when the workflow depends on watertight or closed boundaries.

### Validation and quality

- `validate_mesh(...)` is the compatibility alias for the validation submodule.
- `compute_quality_metrics(mesh)` returns mesh-quality signals that are helpful before training or remeshing.

### Geometry and calculus

- Use mesh geometry helpers for centroids, areas/volumes, normals, curvature, gradients, divergence, curl, and related discrete operators.
- Use spatial query and sampling helpers for nearest cells, barycentric interpolation, and point sampling.

### Repair / remesh / transform

- Repair and remesh helpers are appropriate when the input mesh is imperfect but still simplicial.
- Transformation helpers are useful for rigid transforms, scaling, and workflow alignment.

## Validation checklist

- Point/cell tensor shapes match the simplicial dimension.
- Indices are in bounds and dtypes are integer where required.
- Field ranks match the leading point/cell counts.
- The chosen file format and visualization backend are installed when required.
- The workflow does not assume arbitrary polygon/polyhedron support without conversion.
