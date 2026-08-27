---
name: mesh-and-geometry
description: "Use PhysicsNeMo-Mesh for Mesh/DomainMesh creation, validation,
  geometry/calculus, queries, repair/remesh, I/O, and visualization."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# PhysicsNeMo mesh-and-geometry

Use this sub-skill when the task is about PhysicsNeMo-Mesh objects or mesh preprocessing rather than choosing a neural model or building a data reader.

## Trigger phrases

- `Mesh`, `DomainMesh`, simplicial mesh, triangle mesh, tetrahedral mesh, point cloud, curve mesh.
- Mesh creation, field attachment, `point_data`, `cell_data`, `global_data`, TensorDict field ranks.
- Mesh validation, quality metrics, manifold/watertight checks, duplicate vertices, degenerate or inverted cells.
- Geometry or calculus: centroids, areas/volumes, normals, curvature, gradient, divergence, curl, Laplace-Beltrami.
- Neighbors, adjacency, BVH, spatial query, barycentric sampling/interpolation.
- Mesh repair, cleaning, subdivision, remeshing, transformations/deformation.
- PyVista/VTK conversion, Zarr/native mesh serialization, visualization caveats.

## Fast route

1. **Confirm the representation.** PhysicsNeMo-Mesh accepts pure simplicial complexes: 0-simplices/points, 1-simplices/edges, 2-simplices/triangles, 3-simplices/tetrahedra, or higher-dimensional simplices. Do not treat arbitrary VTK polygons/polyhedra as directly supported until they are triangulated/tetrahedralized or converted through an explicit helper.
2. **Choose object type.** Use `Mesh` for one geometry and `DomainMesh` for an interior mesh plus named boundary meshes.
3. **Import from the right surface.** Root `physicsnemo.mesh` exports only the core object model and field-rank helpers. Validation, I/O, sampling, repair, remeshing, spatial, and calculus functions live in submodules.
4. **Validate before expensive work.** Check tensor shape/dtype/device, out-of-bounds indices, degeneracy, duplicate vertices, and optional manifoldness/inversion. Then compute quality metrics if mesh health matters.
5. **Run operations on the mesh device.** `mesh.to("cuda")` moves geometry and attached data together; PyVista/VTK visualization and conversion are CPU/external-library workflows.
6. **Use references for details.** Recipes: [references/mesh-workflows.md](references/mesh-workflows.md). API/import map: [references/api-reference.md](references/api-reference.md). Failure modes: [references/troubleshooting.md](references/troubleshooting.md).

## Minimal import pattern

```python
from physicsnemo.mesh import DomainMesh, Mesh
from physicsnemo.mesh.validation import compute_quality_metrics, validate

# Compatibility alias exists in the validation submodule, not the mesh root:
from physicsnemo.mesh.validation import validate_mesh  # pending-deprecation alias
```

Never write `from physicsnemo.mesh import validate_mesh`; it is not a root export.

## Validation checklist

- `points`: floating tensor with shape `(n_points, n_spatial_dims)`.
- `cells`: integer tensor with shape `(n_cells, n_manifold_dims + 1)`, same device as `points`; omit it or pass `None` for a point cloud.
- `n_manifold_dims <= n_spatial_dims`; triangles in 3D are valid, tetrahedra in 2D are not.
- Cell indices are in `[0, n_points)` and one cell should not repeat a vertex unless intentionally testing degeneracy.
- `point_data` leaves start with `n_points`; `cell_data` leaves start with `n_cells`; `global_data` has no leading mesh batch dimension.
- For semantic rank schemas, use root field helpers such as `ranks_from_tensordict()` and `validate_data_contains_ranks()`.
- For `DomainMesh`, every boundary value must be a `Mesh` and share the interior spatial dimension; use `dm.validate()` plus `dm.is_boundary_watertight()` when boundary closure matters.

## Sibling routes

- Model-family choice for MeshGraphNet, Transolver, DoMINO, FIGConvNet, or graph/geometry models: route to sibling sub-skill `model-selection`.
- Mesh file readers inside a training data pipeline, including `MeshReader` or `DomainMeshReader`: route to sibling sub-skill `datapipes`.
- Multi-GPU/domain-parallel training after mesh preprocessing: route to sibling sub-skill `distributed-and-domain-parallel`.
- Active-learning loops or ONNX export after mesh-based inference: route to sibling sub-skill `active-learning-and-deployment`.

## Bundled smoke

Run a tiny local check without downloads:

```bash
python sub-skills/mesh-and-geometry/scripts/mesh_smoke.py
python sub-skills/mesh-and-geometry/scripts/mesh_smoke.py --cuda
```

The `--cuda` path only moves a three-point triangle mesh to CUDA when CUDA is available.
