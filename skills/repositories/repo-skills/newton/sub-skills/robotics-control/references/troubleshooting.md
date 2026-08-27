# Robotics-control troubleshooting

## Position targets are shifted or a deprecation warning appears

Symptoms:

- `joint_target_q` indexing works for simple revolute robots but fails after adding a free, ball, or distance joint.
- `ModelBuilder.finalize()` warns about the legacy DOF-shaped target layout.

Recovery:

1. Set `newton.use_coord_layout_targets = True` before creating any `ModelBuilder`.
2. Use coordinate starts for position targets: `model.joint_target_q_start` or `model.joint_q_start`.
3. Continue using DOF starts for velocity targets and generalized effort: `model.joint_qd_start`.
4. Recreate model/control buffers after changing the flag.

## Optional neural policy backend is missing

Symptoms:

- Neural actuator or policy code fails importing ONNX, Warp-NN, or Torch.
- A `.onnx`, `.pt`, `.pth`, or `.pt2` checkpoint cannot be loaded.

Recovery:

- For ONNX workflows, install/verify the `onnx` optional dependency set.
- For Torch checkpoints, install the Torch extra that matches the user's CUDA/Python environment.
- Run `scripts/check_robotics_apis.py --optional-only` before loading a checkpoint.
- Do not download model assets or checkpoints without explicit user approval.

## Label pattern selects no robot or the wrong joints

Newton APIs that accept labels may use glob strings, lists of glob strings, integer indices, or compiled regular expressions.

- Ordinary strings use glob matching such as `robot_*`.
- Compiled regex patterns use full-match semantics; add `.*` for substring behavior.
- `ArticulationView.pattern` matches full articulation labels.
- Joint/link include/exclude filters match final path components.

Print the selected labels from the view before writing arrays.

## IK does not converge or returns a poor pose

Likely causes:

- Target arrays have the wrong shape or dtype.
- Link indices or offsets refer to the wrong frame.
- Joint limits are too tight or not included as objectives.
- The initial seed is far from any solution.
- The problem mixes coordinate and DOF layouts.

Recovery:

1. Use one IK problem and one objective first.
2. Verify target arrays are Warp arrays with shapes expected by the objective.
3. Use `n_seeds`, `noise_std`, or a sampler for difficult problems.
4. Add `IKObjectiveJointLimit` when limits matter.
5. Copy IK coordinates into `joint_target_q` only under coordinate-layout target mode.

## Joint impedance controller rejects a robot

`ControllerJointImpedance` is intended for scalar revolute/prismatic joints plus fixed joints. Free, ball, distance, and other multi-coordinate joints are not valid for its PD error term.

Recovery:

- Build a controller model containing only compatible controlled joints.
- Check `default_dof_indices` length against controlled DOFs.
- Use `(robot_count, max_dofs)` stiffness/damping arrays with padding for heterogeneous batches.
- If the controller model and simulation model differ, document the DOF mapping explicitly.

## Actuator output is double-counted or stale

Actuators scatter-add into output arrays. Zero `control.joint_f` or the configured output buffer before accumulation when multiple actuator calls write the same target. Stateful actuators, delayed actuators, PID controllers, and neural controllers need state buffers swapped each step.
