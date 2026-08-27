# Mesh, USD, and geometry reference

## Public mesh and utility APIs

Useful public utilities include:

- `newton.Mesh`: mesh container with helpers such as primitive mesh creation, `build_sdf()`, convex hull computation, and file/USD constructors where optional dependencies exist.
- `newton.TetMesh`: tetrahedral mesh container with surface triangle and save helpers.
- `newton.Heightfield`: heightfield data for terrain-style collision.
- `newton.Gaussian`: Gaussian/splat-style geometry support.
- `newton.utils.validate_triangle_mesh(vertices, indices, *, min_area=1e-6, max_aspect_ratio=20.0, min_angle_deg=5.0, label=None, stacklevel=2)`.
- `newton.utils.validate_tet_mesh(vertices, indices, *, min_volume=1e-9, min_eta=0.01, label=None, stacklevel=2)`.
- `newton.utils.solidify_mesh(faces, vertices, thickness)`.
- `newton.utils.remesh_mesh(mesh, method="quadratic", recompute_inertia=False, inplace=False, **remeshing_kwargs)`.
- `newton.utils.rasterize_mesh_to_heightfield(...)` for terrain conversion workflows.

Mesh validation warnings are not noise: poor triangles/tets can destabilize inertia, contact, SDF, and remeshing.

## SDF and hydroelastic preparation

SDF contacts and hydroelastic contacts are prepared at the geometry/collision layer:

1. Build or configure SDF data for the shapes that need field queries.
2. Hydroelastic contact requires SDF on both shapes in the interacting pair.
3. Choose SDF resolution and margins before increasing solver iterations.
4. Use Newton `CollisionPipeline`; MuJoCo-native contacts do not provide Newton hydroelastic SDF contact generation.
5. Route contact tuning and buffer sizing to `../solvers-contacts/SKILL.md`.

## USD schema resolver concepts

Newton's USD import system reads standard UsdPhysics attributes and can resolve solver-specific attribute namespaces through public schema resolver classes such as:

- `newton.usd.SchemaResolver`
- `newton.usd.SchemaResolverNewton`
- `newton.usd.SchemaResolverPhysx`
- `newton.usd.SchemaResolverMjc`

Use schema resolvers when the source USD carries Newton, PhysX, or MuJoCo-like custom attributes whose semantics must survive import. If multiple schemas provide related values, keep the resolver list and priority explicit in the import code.

## Deformable USD limits

Newton supports an experimental subset of proposed AOUSD deformable schemas:

- Cables/curves become rod/capsule body chains with cable joints where representable.
- Cloth/surface meshes become particles with FEM triangles and bending edges.
- Volume TetMesh assets become soft bodies.
- Unsupported or malformed inputs warn and are skipped or preserved as metadata; they should not silently become different physical models.

Known limitations include rest-state handling, compliant attachments, vendor-native PhysX/Omni deformable assets, per-element material bindings, some collision participation details, and certain topology edge cases. Treat these as version-sensitive and verify with a focused asset before building a larger pipeline.

## Optional dependency map

| Workflow | Likely extra/module |
| --- | --- |
| USD core and schemas | `newton[importers]`, `pxr`, `newton_usd_schemas` |
| MJCF and MuJoCo solver | `newton[sim]`, `mujoco`, `mujoco_warp` |
| Mesh processing | `newton[importers]`, `trimesh`, `meshio`, `scipy`, `fast_simplification`, `coacd` |
| Open3D or pyfqmr remeshing | `newton[remesh]` or `newton[importers]` where wheels exist |
| URI resolution | `newton[importers]`, `resolve-robotics-uri-py`, `requests` |

Run `scripts/check_import_extras.py` before deciding whether an import failure is a bad asset or a missing optional dependency.
