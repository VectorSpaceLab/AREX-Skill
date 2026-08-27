# Cross-Cutting Troubleshooting

Read this for a failure that spans more than one sub-skill. Route the detailed
workflow to the nearest owner after identifying the boundary.

## Missing or replaced dependencies

- **Symptom:** `ModuleNotFoundError` for `isaacgym`, `torch`, `rsl_rl`,
  `hydra`, or `mpc_osqp`.
- **Action:** run the setup sub-skill's advisory and strict probes. Initialize
  the pinned native inputs, use the documented Python-era environment, install
  the project editable, and re-run `pip check`.
- **Important:** Isaac Gym Preview 4 is a separate closed-source dependency.
  CUDA visibility and PyTorch import do not prove it. Keep RL/simulation
  blocked until both `isaacgym.gymapi` and `isaacgym.gymtorch` import.

## Pip changes the Torch stack

- **Symptom:** installing RSL-RL replaces PyTorch 1.10/CUDA 11.3 with a newer
  Torch or CUDA wheel, or `pip check` reports a missing companion package.
- **Action:** start with a fresh isolated environment, install the documented
  Torch/CUDA foundation first, then install the pinned RSL-RL checkout with
  dependency resolution disabled (`--no-deps`), and finally build this project.
  Do not repair a mixed binary stack by repeatedly upgrading packages in place.

## Compiled solver cannot import

- **Symptom:** `import mpc_osqp` fails, symbols such as `ConvexMpc` are missing,
  or the extension build cannot find Eigen, pybind11, qpOASES, or OSQP headers.
- **Action:** run `check_mpc_extension.py` without `--build` first; verify the
  four declared submodule commits and OSQP source/layout; rebuild with the
  public editable command only after the compiler/header prerequisites are
  present. Route API and torque-shape questions to `mpc-control`.

## Config, asset, or checkpoint mismatch

- **Symptom:** an RL task name is rejected, a YAML interpolation is missing, a
  URDF mesh cannot be found, or a checkpoint path silently falls back to a
  different run.
- **Action:** run the read-only config validator for all tasks, then pass an
  explicit checkpoint path and confirm it is a regular non-empty file. A `.pt`
  or `.pth` suffix does not prove RSL-RL compatibility. Do not alter the
  observation/action dimensions for an existing policy without treating it as a
  new model.

## Viewer, gamepad, or long-running command

- **Symptom:** a headless process waits for a viewer, gamepad import/device, or
  training loop; a machine appears hung.
- **Action:** stop the process safely, verify the Isaac Gym gate, use
  `--disable-gamepad` where supported, use `headless=True` for training, and
  run bundled diagnostics rather than a full simulation as a smoke test.
  Viewer/gamepad cleanup must destroy the viewer/simulation and stop the input
  thread on every exit path.

## Numerical or control failure

- **Symptom:** unstable gait, wrong leg signs, exploding solver values, or
  controller output with the wrong shape.
- **Action:** verify robot-specific joint conventions, 12 torque ordering,
  state frame/quaternion order, command units, nonnegative 13-element MPC
  weights, and the controller timestep. Check that commands are copied into
  per-instance records rather than sharing mutable arrays. A static import or
  solver pass is not evidence of gait stability.

## Escalation boundary

If the issue needs a different simulator, real-robot hardware, a vendor SDK,
credentials, an external license, or a long training run, state the missing
prerequisite and stop. Do not silently substitute another backend or claim
sim-to-real readiness.
