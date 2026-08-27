# PhysicsNeMo mesh API reference

| Object / function | Key fact |
| --- | --- |
| `physicsnemo.mesh.Mesh` | Core simplicial mesh object with `point_data`, `cell_data`, and `global_data`. |
| `physicsnemo.mesh.DomainMesh` | Interior mesh plus named boundary meshes. |
| `physicsnemo.mesh.flatten_rank_spec` / `rank_counts` / `ranks_from_tensordict` / `validate_data_contains_ranks` | Field-rank helpers for mesh-associated data. |
| `physicsnemo.mesh.validation.validate_mesh` | Validation entry point in the validation submodule. |
| `physicsnemo.mesh.validation.validate` | Lower-level validation helper. |
| `physicsnemo.mesh.validation.compute_quality_metrics` | Mesh quality summary helper. |
| `physicsnemo.mesh.io.to_zarr` / `from_zarr` | Mesh serialization helpers. |
| `physicsnemo.mesh.io.to_pyvista` / `from_pyvista` | PyVista interop helpers. |
| `physicsnemo.mesh.geometry.*` | Areas, volumes, normals, curvature, gradients, and related geometry operators. |
| `physicsnemo.mesh.sampling.*` | Barycentric sampling, point matching, and nearest-cell helpers. |
| `physicsnemo.mesh.remeshing.*` | Remeshing and partition helpers. |
| `physicsnemo.mesh.repair.*` | Cleaning and topology repair helpers. |
| `physicsnemo.mesh.transformations.*` | Transform, translate, rotate, and scale helpers. |

## Practical notes

- Root `physicsnemo.mesh` is intentionally small; the deeper operations live in submodules.
- `validate_mesh` is part of the validation submodule, not the mesh root.
- The main object model is simplicial, so cell shapes and dimensionality matter.
