# Solver and contact troubleshooting

## Missing MuJoCo or solver optional dependency

Symptoms:

- `ModuleNotFoundError: mujoco` or `ModuleNotFoundError: mujoco_warp` when constructing `SolverMuJoCo`.
- Optional solver imports fail only when the class is used.

Recovery:

1. Install only the required extra, for example `pip install "newton[sim]"` for MuJoCo workflows.
2. Re-run the root `scripts/check_newton_env.py --show-optional`.
3. If MuJoCo is not essential, switch to `SolverXPBD`, `SolverSemiImplicit`, or `SolverFeatherstone` depending on coordinate needs.

## Solver and coordinate mismatch

Symptoms include static-looking bodies, wrong initial pose, or contacts at the origin.

- Generalized-coordinate state lives in `joint_q`/`joint_qd`.
- Maximal-coordinate state lives in `body_q`/`body_qd`.
- Collision detection needs current body poses.

Call `newton.eval_fk(model, model.joint_q, model.joint_qd, state)` after editing generalized coordinates and before maximal-coordinate solvers or collision checks.

## Unsupported joint or geometry

MuJoCo, VBD, Kamino, MPM, Style3D, XPBD, and Featherstone do not support identical feature sets. When a solver rejects a joint/geometry:

1. Check whether the feature is solver-specific or experimental.
2. Use the solver-selection matrix.
3. For MuJoCo, remember that some Newton shapes/custom attributes are mapped, dropped, or converted.
4. For cables, cloth, soft bodies, and MPM, use the solver family that owns that material.

## Contact buffer capacity or contact count surprises

Symptoms:

- Contact count is truncated.
- Dense SDF/hydroelastic scenes miss expected contacts.
- Performance collapses after enabling mesh contacts.

Recovery:

1. Prove a primitive scene has contacts.
2. Print or inspect contact capacities and expected shape pairs.
3. Increase `rigid_contact_max`, shape-pair capacity, or contact reduction settings only after geometry filters are correct.
4. For SDF/hydroelastic, reduce mesh complexity or SDF resolution before increasing every buffer.

## Hydroelastic/SDF path does not activate

Likely causes:

- One or both shapes lack SDF data.
- The pipeline uses MuJoCo-native contacts instead of Newton contacts.
- The shapes are filtered, in different worlds, or collision-disabled.
- The mesh is non-watertight or has invalid scale/topology.

Route mesh/SDF asset preparation to `../asset-import-export/SKILL.md`, then return here for solver integration.

## Instability or NaNs after tuning

1. Revert to a tiny sphere/ground model with `SolverXPBD`.
2. Reduce `dt` and increase substeps.
3. Check mass/inertia and initial overlap.
4. Tune material gains before solver-specific advanced options.
5. Use `.numpy()` to inspect arrays; it synchronizes the device copy.
6. Treat CUDA-only failures as backend issues until reproduced on CPU or a smaller GPU case.

## Determinism mismatch

Floating-point and contact-order differences are expected across devices and solver settings. If deterministic behavior is required, choose deterministic options where exposed, fix device and backend, avoid unnecessary contact reordering, and validate with tolerances anchored to the task rather than exact array equality.
