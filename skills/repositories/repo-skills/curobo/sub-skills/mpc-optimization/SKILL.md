---
name: mpc-optimization
description: "Configures cuRobo trajectory optimization, rollout costs, and CUDA
  MPC loops for smooth, collision-aware robot control."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Optimization and MPC

Use this route for B-spline trajectory optimization, MPC action sequences,
custom costs/rollouts, optimizer stages, or reactive control design. Read
[api-reference.md](references/api-reference.md) and
[workflows.md](references/workflows.md) before constructing internal configs.

## Core workflow

1. Choose `TrajectoryOptimizerCfg.create` for offline trajectory generation or
   `ModelPredictiveControlCfg.create` for receding-horizon control. Keep robot,
   optimizer, rollout, transition, metrics, and scene YAMLs from compatible
   families.
2. Configure `DeviceCfg`, collision/self-collision, tolerances, horizon/dt,
   seeds, and `use_cuda_graph=True`. Construct only after a CUDA probe.
3. For trajopt, call `solve_pose`, `solve_cspace`, or `solve_state`; inspect
   convergence, costs, collision metrics, and interpolated trajectory.
4. For MPC, update current state and goal/tool pose, then call
   `optimize_next_action` or `optimize_action_sequence`. Warm-start from the
   previous solution and use safe deceleration on failure.
5. Disable graphs only in a bounded debug/test pass. The included
   [scripts/optimization_smoke.py](scripts/optimization_smoke.py) checks
   configuration and optimizer construction without a long control loop.

For scene schemas use [collision-scenes](../collision-scenes/SKILL.md); for a
composed planner use [motion-planning](../motion-planning/SKILL.md).
