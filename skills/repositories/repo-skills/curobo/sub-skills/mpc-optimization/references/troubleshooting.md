# Optimization troubleshooting

- **Config resolution error:** check each optimizer/metrics/transition YAML and
  use the public factory; do not combine old v1 config names with v2 dataclasses.
- **Divergent or invalid trajectory:** inspect joint bounds, dt/horizon,
  transition model, seed quality, cost weights, and collision metrics.
- **MPC action shape error:** record `(batch,horizon,action_dim)`, control-point
  count, interpolation steps, and configured environments before resetting shape.
- **Online failure:** distinguish no convergence from collision/limit violation;
  invoke safe deceleration, retain diagnostics, and retry with a warm start or
  bounded cold start.
- **CUDA graph capture failure:** use eager mode to locate dynamic allocation or
  shape mutation, then restore graph mode after fixing stable shapes.
- **OOM/latency:** lower seeds, horizon, batch, or optimization iterations;
  select a free GPU before changing numerical tolerances.
