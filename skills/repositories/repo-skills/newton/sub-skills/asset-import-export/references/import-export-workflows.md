# Import and export workflows

## Public import methods

Installed inspection confirmed these public builder methods:

```python
builder.add_urdf(source, *, xform=None, floating=None, base_joint=None, parent_body=-1, scale=1.0, hide_visuals=False, parse_visuals_as_colliders=False, up_axis=newton.Axis.Z, force_show_colliders=False, enable_self_collisions=True, ignore_inertial_definitions=False, joint_ordering="dfs", bodies_follow_joint_ordering=True, collapse_fixed_joints=False, collapse_massless_fixed_root=False, mesh_maxhullvert=None, force_position_velocity_actuation=False, override_root_xform=False)

builder.add_mjcf(source, *, xform=None, floating=None, base_joint=None, parent_body=-1, armature_scale=1.0, scale=1.0, hide_visuals=False, parse_visuals_as_colliders=False, parse_meshes=True, parse_sites=True, parse_visuals=True, parse_mujoco_options=True, up_axis=newton.Axis.Z, ignore_names=(), ignore_classes=(), visual_classes=("visual",), collider_classes=("collision",), no_class_as_colliders=True, force_show_colliders=False, enable_self_collisions=True, ignore_inertial_definitions=False, collapse_fixed_joints=False, collapse_massless_fixed_root=False, verbose=False, skip_equality_constraints=False, convert_mjc_equality_constraints=True, convert_3d_hinge_to_ball_joints=False, mesh_maxhullvert=None, ctrl_direct=False, path_resolver=None, override_root_xform=False, legacy_margin_gap=False)

builder.add_usd(source, *, xform=None, floating=None, base_joint=None, parent_body=-1, only_load_enabled_rigid_bodies=False, only_load_enabled_joints=True, joint_drive_gains_scaling=1.0, verbose=False, ignore_paths=None, collapse_fixed_joints=False, enable_self_collisions=True, apply_up_axis_from_stage=False, root_path="/", joint_ordering="dfs", bodies_follow_joint_ordering=True, skip_mesh_approximation=False, load_sites=True, load_visual_shapes=True, load_static_visual_shapes=True, hide_collision_shapes=False, force_show_colliders=False, parse_mujoco_options=True, mesh_maxhullvert=None, schema_resolvers=None, force_position_velocity_actuation=False, convert_mjc_equality_constraints=True, override_root_xform=False, legacy_margin_gap=False, return_deformable_results=False)
```

## Format selection

- Use URDF for conventional robot descriptions with links, joints, inertials, and meshes.
- Use MJCF when the source is MuJoCo XML or when MuJoCo solver/custom-attribute semantics matter.
- Use USD for rich scene hierarchies, UsdPhysics, Newton/PhysX/MuJoCo-style schema attributes, cameras/sites, and deformable proposal data.

After import, route solver/contact questions to `../solvers-contacts/SKILL.md` and control/IK questions to `../robotics-control/SKILL.md`.

## Common import flags

- `floating` and `base_joint` decide root mobility.
- `parent_body` attaches an imported model under an existing body.
- `scale` changes geometry and distances; re-check mass/inertia behavior after scaling.
- `hide_visuals`, `parse_visuals_as_colliders`, `load_visual_shapes`, and `hide_collision_shapes` control visual-vs-collider interpretation.
- `enable_self_collisions` affects generated collision filters.
- `collapse_fixed_joints` and `collapse_massless_fixed_root` can simplify topology, but change labels and joint counts.
- `mesh_maxhullvert` controls convex hull complexity for mesh collision conversions.
- `joint_ordering` and `bodies_follow_joint_ordering` matter when downstream code expects stable indexing.
- `legacy_margin_gap` exists for migration of older margin/gap conventions; do not use it casually in new assets.

## MJCF and MuJoCo attributes

For MJCF workflows, decide whether the target solver is MuJoCo or another Newton solver:

1. Import with `add_mjcf(..., parse_mujoco_options=True)` when MuJoCo-authored solver/contact options should be preserved.
2. If using `SolverMuJoCo`, install/verify `newton[sim]` and construct `SolverMuJoCo` after the model is finalized.
3. If using Newton contacts with MuJoCo dynamics, pass `use_mujoco_contacts=False` to the solver and create a `CollisionPipeline`.
4. If converting 3D hinge/equality behavior, keep conversion flags explicit in the code so downstream agents can review semantic changes.

## USD workflow

Use `add_usd()` when assets carry UsdPhysics, Newton custom attributes, deformable proposal APIs, or external solver schemas. Typical decisions:

- `root_path` limits import scope.
- `schema_resolvers` controls how Newton, PhysX, or MuJoCo-like custom attributes are interpreted.
- `apply_up_axis_from_stage` can align stage units/orientation.
- `return_deformable_results=True` returns maps that identify imported cable, cloth, soft-body, and attachment ranges by prim path.

Do not silently import unsupported deformables as a different physical model. Preserve warnings and route to troubleshooting if the source uses unimplemented schemas or malformed topology.

## Export and artifact routes

Newton's main export-style user workflows are viewer-backed:

- `newton.viewer.ViewerUSD(output_path, fps=60, up_axis="Z", num_frames=100, ...)` writes USD scene/time samples.
- `newton.viewer.ViewerFile(output_path, auto_save=True, ...)` records state snapshots.

For live viewer behavior, headless mode, recordings, and example CLI options, use `../sensors-visualization/SKILL.md`.
