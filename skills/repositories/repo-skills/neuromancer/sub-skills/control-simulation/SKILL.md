---
name: control-simulation
description: "Assemble safe NeuroMANCER open- and closed-loop rollouts with
  System, preview, moving-horizon, and PSL simulators; use this route for
  control wiring, signals, normalization, and external-data boundaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Control simulation

Use this sub-skill when a task needs a short, inspectable NeuroMANCER rollout,
a differentiable closed loop, reference preview, moving-horizon inputs, or a
PSL plant/emulator. It is verified against the `neuromancer==1.5.6` API surface
and is CPU-first. Start with [the API contract](references/api-reference.md),
then select a bounded procedure from [the workflows](references/workflows.md).
Use [troubleshooting](references/troubleshooting.md) before changing tensor
axes, keys, padding, or backends.

## Route by intent

- **Neural or symbolic nodes in a rollout:** use `Node` and `System`; keep
  objective, constraint, and loss syntax in the symbolic-problems route.
- **Future-known references or disturbances:** use `SystemPreview` and make
  the preview length and end-of-sequence padding explicit.
- **A model that consumes a short time history:** wrap its `Node` in
  `MovingHorizon`; reset or replace its history between independent episodes.
- **A ground-truth or synthetic plant:** choose a named entry in
  `neuromancer.psl.systems`, then use a short `simulate` call with an explicit
  backend and seed.
- **Learned differentiable predictive control:** compose policy and plant
  nodes in a closed-loop `System`; follow the recipe in the workflow reference
  and send objectives/constraints to symbolic-problems.
- **Recorded or domain data:** first establish a local file/schema and data
  permission. Do not silently invoke a PSL download or a long building/control
  example.

## Minimum safe procedure

1. Decide the time convention: per-node tensors are `(batch, features)`;
   rollout dictionaries are `(batch, time, features)`. Give the system a
   one-step initial state and a time-bearing exogenous key or an explicit
   `nsteps`.
2. Give every node an explicit unique name and order nodes so outputs needed by
   a later node already exist in the current step. Use the same key for a
   recurrent state transition only when that overwrite is intentional.
3. Run `scripts/simulation_smoke.py --run` or an equivalent four-step CPU
   fixture before adding a real plant, preview, loss, or trainer.
4. For PSL, choose NumPy first for a non-differentiable check or CPU Torch when
   gradients are needed. Use `set_stats=False` for a bounded structural smoke
   unless statistics and normalizers are part of the test.
5. Record shapes, keys, horizon, seed, backend, padding policy, and any
   external-data prerequisite. Treat GPU, network, credentials, and long
   training as separate optional verification.

The generated graph owns wiring and simulation knowledge only. Route general
sequence batching/training to data-training, neural blocks/integrators to
dynamics-modeling, symbolic objectives and constraints to symbolic-problems,
and structured maps to structured-operators.
