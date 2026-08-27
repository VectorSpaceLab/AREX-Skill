# Parity and Diagnostic Workflows

## Define the experiment

Before comparing two backends, pin:

- exact RoboVerse/MetaSim source and package versions;
- task id, robot, scene/assets, simulator and renderer;
- number of environments, device, timestep/control rate, seed and reset state;
- identical action sequence or identical policy/checkpoint;
- observation keys/order, reward terms, termination/truncation semantics;
- metric, tolerance, sample count, and output artifact.

Run a bounded end-to-end rollout first. Then compare aligned tensors. A parity
claim should include backend names, number of steps, max/mean absolute delta,
relative delta where meaningful, and the first divergent field/time.

## Comparison levels

1. **Registration:** task/package is discoverable in both intended environments.
2. **Construction:** same config resolves and reset succeeds.
3. **Observation:** same keys/shapes/order and numerical values under aligned
   state.
4. **Reward/termination:** compare each reward term, success, terminated, and
   truncated separately.
5. **Closed-loop:** execute the same policy and report trajectory divergence;
   this is not implied by observation parity.
6. **Rendering:** compare images only after camera, renderer, resolution, and
   lighting are controlled; visual similarity alone is not dynamics parity.

## Common diagnostics

- `verify_native_registration.py`-style audits check package discovery and task
  lookup without claiming a backend.
- cartpole observation/reward parity scripts are useful methodology for aligned
  state and deltas, but require the exact simulator extras.
- Go1, LIBERO+, SimplerEnv, RobotWin, MJLab, and robosuite scripts may need
  assets, native packages, GPU, display, or policy/data. Treat them as
  reference-only until those prerequisites are explicitly prepared.
- For a numerical mismatch, compare units, quaternion convention, joint/body
  ordering, action scaling, reset randomization, contact solver, timestep,
  reward clipping, and termination timing before changing code.

## Status vocabulary

Use `PASS` only for the exact selected backend/metric. Use `NATIVE_FAIL` for a
real reproducible failure, `BLOCKED_REQUIRED_BACKEND` when a required runtime is
unavailable, and `SKIP_NOT_SELECTED`/`SKIP_UNSAFE` for optional or unsafe paths.
Never turn a missing backend into a numerical parity pass.
