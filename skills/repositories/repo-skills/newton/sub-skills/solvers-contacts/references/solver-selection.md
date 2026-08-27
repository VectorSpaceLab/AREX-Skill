# Solver selection

Use this reference after the model topology is known. If the model does not yet build, route back to `../modeling-simulation/SKILL.md`.

## Public solver constructors

Installed inspection confirmed these public classes under `newton.solvers`:

- `SolverXPBD(model, *, iterations=2, soft_body_relaxation=0.9, soft_contact_relaxation=0.9, joint_linear_relaxation=0.7, joint_angular_relaxation=0.4, joint_linear_compliance=0.0, joint_angular_compliance=0.0, rigid_contact_relaxation=0.8, rigid_contact_con_weighting=True, angular_damping=0.0, enable_restitution=False, deterministic=None)`
- `SolverSemiImplicit(model, *, angular_damping=0.05, friction_smoothing=1.0, joint_attach_ke=10000.0, joint_attach_kd=100.0, enable_tri_contact=True, deterministic=None)`
- `SolverFeatherstone(model, *, angular_damping=0.05, update_mass_matrix_interval=1, friction_smoothing=1.0, use_tile_gemm=False, fuse_cholesky=True, deterministic=None)`
- `SolverMuJoCo(model, *, separate_worlds=None, iterations=None, solver=None, integrator=None, use_mujoco_cpu=False, save_to_mjcf=None, use_mujoco_contacts=True, include_sites=True, skip_visual_only_geoms=True, deterministic=None, ...)`
- `SolverVBD(model, *, iterations=10, integrate_with_external_rigid_solver=False, particle_enable_self_contact=False, rigid_compliant_alm=None, rigid_contact_hard=True, deterministic=None, ...)`
- `SolverImplicitMPM(model, config, *, temporary_store=None, verbose=None, enable_timers=False)`
- `SolverStyle3D(model, *, iterations=10, linear_iterations=10, drag_spring_stiff=100.0, enable_mouse_dragging=False)`
- `SolverKamino(model, config=None)`

Some constructors import optional dependencies lazily. If construction fails with a missing module, install the smallest extra for that workflow and re-run the environment check.

## Coordinate and feature routing

| Need | Prefer | Why | Notes |
| --- | --- | --- | --- |
| Small public rigid/soft body smoke | `SolverXPBD` | Stable public default for many examples; consumes Newton contacts | Call `eval_fk()` before collision when using generalized coordinates |
| Maximal-coordinate rigid/particle scene | `SolverXPBD` or `SolverSemiImplicit` | Works with Newton `CollisionPipeline` | Tune iterations/substeps before gains |
| Generalized-coordinate articulated robot | `SolverMuJoCo` or `SolverFeatherstone` | Uses generalized coordinates | MuJoCo needs `newton[sim]`; Featherstone is base-package |
| MuJoCo/MJCF semantics or custom attrs | `SolverMuJoCo` | Maps Newton model to MuJoCo/MuJoCo Warp | Decide `use_mujoco_contacts` explicitly |
| Cloth, cables, VBD soft/rigid contact | `SolverVBD` | VBD/AVBD paths and cable joints | Experimental; verify selected feature support |
| MPM granular/elasto-plastic materials | `SolverImplicitMPM` | MPM-specific config | Use examples/tests as evidence; often heavier |
| Style3D cloth | `SolverStyle3D` | Projective dynamics cloth route | Feature-specific, not a generic rigid solver |
| Kinematic loops/hard frictional contacts | `SolverKamino` | Experimental constrained mechanisms | Public API/behavior may change |
| Multi-physics coupling | coupled solver APIs | Combines entry solvers/views | Keep entry states and contact views consistent |

## Contact passing rules

- Solvers that consume Newton contacts need a `CollisionPipeline` and `Contacts` buffer.
- `SolverMuJoCo` defaults to MuJoCo-native contacts with `use_mujoco_contacts=True`; pass `contacts=None` in that path.
- To use Newton SDF/hydroelastic/contact matching with MuJoCo dynamics, create `SolverMuJoCo(..., use_mujoco_contacts=False)`, run `CollisionPipeline.collide()`, and pass Newton contacts to `step()`.
- If no contacts are expected, pass `None` only after verifying the solver supports that case.

## Selection workflow

1. Identify model state representation: generalized articulation or maximal rigid/particle representation.
2. Identify materials: rigid only, cloth, soft body, MPM, cable, or coupled.
3. Identify contacts: none, MuJoCo-native, Newton primitive, SDF, hydroelastic, contact matching, or soft/rigid.
4. Check optional dependency and hardware requirements.
5. Run the smallest solver smoke (`scripts/compare_solver_step.py`) before full examples.
6. Tune substeps/iterations, then material/contact gains, then advanced deterministic/backend settings.

## Experimental features

Kamino and VBD public API/behavior are documented as experimental. Generated code should isolate them behind clear feature checks and avoid broad claims of stability. If a task needs exact behavior, verify against the installed Newton version and a focused native example or test.
