---
name: robotics-modules
description: "Use PyPose's differentiable robotics modules for discrete
  dynamics, Bayesian state estimation, LQR/MPC control, IMU preintegration,
  PnP/ICP pose solving, and rotation geodesic loss; choose constructors and
  tensor contracts from the bundled references, validate
  shapes/covariances/units, and compose modules without confusing them with
  primitive manifold math, generic optimization, or geometry metrics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# PyPose robotics-modules

Use this skill when a Researcher needs PyPose's high-level robotics modules in
`pypose.module`: system models (`System`, `LTI`, `LTV`, `NLS`), EKF/UKF/PF,
LQR/MPC, `IMUPreintegrator`, `EPnP`, `ICP`, or `GeodesicLoss`. The module
implementations are differentiable PyTorch `nn.Module`s, but several modules
also mutate a clock, integration state, or stopping planner. Treat those state
and shape contracts as part of the API.

## Scope boundary

- **Included:** constructors, forward signatures, rightmost feature dimensions,
  leading-batch broadcasting, time and reset behavior, covariance contracts,
  dynamics/filter/control composition, IMU units and frame conventions, PnP and
  ICP initialization, and solver-stepper diagnostics.
- **Excluded:** primitive LieTensor/manifold algebra (`lie-tensor`), generic
  Gauss--Newton/Levenberg--Marquardt optimization (`optimization`), and
  geometry/spline/trajectory metrics (`geometry-evaluation`). `EPnP(refine=True)`
  may call its own internal refinement; use the PnP contract here rather than
  treating that implementation detail as a general optimizer workflow.

Read the smallest relevant reference before writing code:

- [api-reference.md](references/api-reference.md) for verified signatures and
  exact call/return contracts.
- [state-estimation.md](references/state-estimation.md) for `System`/`NLS`
  models and EKF/UKF/PF covariance and shape rules.
- [control-and-dynamics.md](references/control-and-dynamics.md) for LTI/LTV,
  LQR, MPC, horizon layouts, and stepper behavior.
- [imu-and-geometric-solvers.md](references/imu-and-geometric-solvers.md) for
  IMU, EPnP, ICP, and geodesic rotation loss.
- [troubleshooting.md](references/troubleshooting.md) for failure diagnosis and
  safe recovery.

## Operating workflow

1. **Identify the module boundary.** Decide whether the task needs a dynamic
   model, a state estimator, a controller, sensor preintegration, a geometric
   solver, or a rotation loss. Do not replace a module with primitive manifold
   operations unless the task explicitly needs those primitives.
2. **Normalize shapes before constructing modules.** Put features in the last
   dimension, matrices in the last two dimensions, and batch/time axes in
   leading positions. Make `dtype` and `device` consistent across model,
   covariance, costs, and observations. Do not rely on accidental broadcasting
   for state versus time axes.
3. **Build the dependency chain.** A normal filtering chain is
   `NLS -> (EKF | UKF | PF)`; a control chain is `NLS -> set_refpoint -> LQR`
   inside `MPC`; a sensor chain is `IMUPreintegrator -> pose/velocity/position`
   consumers. `EPnP` and `ICP` each return an `SE3` pose for a separate
   geometry-registration branch, while `GeodesicLoss` compares rotations.
4. **Make mutable state explicit.** Reset a dynamic model before replaying a
   trajectory. Reuse an IMU integrator only when its accumulation semantics are
   intended. Reuse a `ReduceToBason`-like stepper only after its `reset()`.
   Avoid concurrent calls through one mutable module.
5. **Check outputs, not just execution.** Assert expected trailing shapes,
   finiteness, covariance symmetry/positive semidefiniteness within numerical
   tolerance, plausible units, and an error or cost that improves on a
   deterministic fixture. Use the bundled scripts for a quick CPU check:

   From the `pypose` skill directory, run:

   ```bash
   python sub-skills/robotics-modules/scripts/filter_smoke.py
   python sub-skills/robotics-modules/scripts/icp_smoke.py
   ```

   The helpers can also be invoked by absolute path from any working directory.

## Composition patterns

### Dynamics and filtering

Subclass `NLS`, implement pure `state_transition(state, input, t)` and
`observation(state, input, t)`, and call the model with `(state, input)` for one
step. `NLS.forward` evaluates both functions at the current clock and its hook
increments the clock afterwards. Call `set_refpoint` before reading `A`, `B`,
`C`, `D`, `c1`, or `c2`; this computes Jacobians at the selected state/input/time.
Then give the same model to one filter and call it with an estimate, a
measurement, an input, and a covariance. The filter's direct model evaluations
are not a substitute for adding process/measurement noise to the actual data.

For a linear problem, use `LTI` or a time-indexed `LTV` instead of making a
linear `NLS`; their matrices can be fed directly to LQR. See the exact time
semantics and observation timing in the references.

### Control

Use `LQR(system, Q, p, T)` for one finite-horizon solve. `Q` covers the
concatenated `[state, input]` vector and `p` has the same final feature size.
Use `MPC` around the same system and costs when nonlinear dynamics require
relinearization. `MPC.forward` performs iterative LQR under `no_grad`, selects a
best iterate using its mutable stepper, and makes a final LQR call; set a small,
explicit stepper for tests and deterministic examples.

### Sensor and pose branches

`IMUPreintegrator` consumes body-frame angular rates/accelerations and positive
finite time intervals, returning incrementally propagated pose, velocity,
position, and optionally a 9x9 covariance. `EPnP` estimates an `SE3` from at
least four 3D/2D correspondences and camera intrinsics. `ICP` estimates an `SE3`
from source/target point clouds by nearest-neighbor matching and SVD; it is
local and initialization-sensitive. Keep these frame conventions documented at
call sites instead of silently composing poses in an inverse order.

## Verification gates

Before handing off code that uses this skill:

- import and constructor signatures match [api-reference.md](references/api-reference.md);
- a minimal deterministic call succeeds from a clean current working directory;
- all tensors have declared trailing shapes and common dtype/device;
- filter `P`, `Q`, and `R` are square in their intended state/observation spaces;
- dynamics clock/reset and IMU accumulation/reset behavior are tested;
- LQR/ICP/MPC stepper limits are explicit for tests;
- geometric inputs meet point-count, intrinsics, non-degeneracy, and
  initialization requirements; and
- no smoke helper downloads data, plots, writes outside an explicitly selected
  output, or depends on the caller's working directory.

The references summarize the verified public module contracts and synthetic
smoke scripts; a Researcher does not need the original source checkout or
example files to use this sub-skill.
