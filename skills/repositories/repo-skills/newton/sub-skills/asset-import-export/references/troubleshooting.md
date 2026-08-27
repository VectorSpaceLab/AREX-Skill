# Asset import/export troubleshooting

## Missing optional dependency

Symptoms:

- `ModuleNotFoundError: pxr`, `newton_usd_schemas`, `mujoco`, `mujoco_warp`, `trimesh`, `open3d`, or similar.
- Import method works for primitives but fails for URDF/MJCF/USD/mesh assets.

Recovery:

1. Run `scripts/check_import_extras.py`.
2. Install the smallest matching extra: `newton[sim]`, `newton[importers]`, `newton[remesh]`, or `newton[examples]`.
3. Re-run the import with the same flags. Do not install Torch/RTX/notebook extras unless the task actually needs them.

## Asset path or URI cannot be resolved

Likely causes:

- Relative mesh paths are resolved from a different directory than expected.
- URDF/MJCF `package://`, `model://`, or custom asset paths need a resolver.
- Network-backed or external asset downloads are blocked.

Recovery:

- Prefer explicit absolute asset paths in user code and document any root directory assumptions.
- For MJCF, use `path_resolver` when the file refers to nonstandard locations.
- Avoid hidden downloads in generated scripts; ask the user before network retrieval.

## Imported model has wrong topology or labels

Flags that change topology include `collapse_fixed_joints`, `collapse_massless_fixed_root`, `joint_ordering`, `bodies_follow_joint_ordering`, `ignore_paths`, `ignore_names`, `ignore_classes`, and visual/collider parsing flags.

Recovery:

1. Print counts before and after changing flags.
2. Preserve labels that downstream controllers, sensors, and `ArticulationView` patterns depend on.
3. Disable fixed-joint collapse while debugging index mismatches.
4. Re-enable simplification only after tests do not depend on removed joints/bodies.

## Visuals become colliders or colliders disappear

Check `parse_visuals_as_colliders`, `hide_visuals`, `load_visual_shapes`, `load_static_visual_shapes`, `hide_collision_shapes`, `force_show_colliders`, and per-format visual/collider class filters.

Start with explicit collider geometry, then add visual shapes once contacts are correct.

## Mesh quality warnings

Warnings from triangle/tet validation, hull generation, SDF building, or remeshing usually indicate real physical risks: degenerate triangles, bad aspect ratios, non-watertight meshes, tiny volumes, or invalid scale.

Recovery:

- Run validation utilities before SDF/hydroelastic workflows.
- Reduce mesh complexity before raising contact buffers.
- Use remeshing only with the optional modules installed and with a copy of the mesh unless `inplace=True` is intended.
- Recompute inertia when geometry changes materially.

## USD deformable import warns or skips assets

Newton intentionally supports only a bounded experimental subset of deformable USD inputs. If a cable/cloth/volume is skipped, do not silently fall back to a rigid import. Capture the warning, inspect authored schema/attributes, and either adjust the asset or mark the feature unsupported for that Newton version.

## MuJoCo custom attributes not affecting simulation

Ensure MJCF/USD import preserved MuJoCo options and that `SolverMuJoCo` is the solver actually used. Newton force-space contact gains, MuJoCo raw `solref`/`solimp`, and Newton contacts are different routes; choose one explicitly and route contact semantics to `../solvers-contacts/SKILL.md`.
